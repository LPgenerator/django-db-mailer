"""Tests for dbmail.models — ApiKey security and JSON dual-write."""

from __future__ import annotations

import hashlib

import pytest

pytestmark = pytest.mark.django_db


# ---------------------------------------------------------------------------
# ApiKey security
# ---------------------------------------------------------------------------


class TestApiKeySave:
    def test_save_autohashes_when_password_hash_empty(self):
        from dbmail.models import ApiKey

        obj = ApiKey.objects.create(name="t", api_key="a" * 32)
        assert obj.password_hash != ""
        assert obj.password_hash != "a" * 32

    def test_cache_key_is_sha256_not_raw(self, api_key):
        from dbmail.models import ApiKey

        cache_key = ApiKey._cache_key(api_key.api_key)
        sha = hashlib.sha256(api_key.api_key.encode("utf-8")).hexdigest()
        assert cache_key == "dbmail:apikey:" + sha
        assert api_key.api_key not in cache_key

    def test_clean_cache_drops_legacy_and_hashed_entries(self, api_key):
        from django.core.cache import cache

        cache.set(api_key.api_key, 1, timeout=60)
        cache.set(api_key._cache_key(api_key.api_key), 1, timeout=60)
        api_key._clean_cache()
        assert cache.get(api_key.api_key) is None
        assert cache.get(api_key._cache_key(api_key.api_key)) is None


class TestApiKeyIsValid:
    def test_correct_key_returns_true(self, api_key):
        assert api_key.is_valid_key("x" * 32) is True

    def test_wrong_key_returns_false(self, api_key):
        assert api_key.is_valid_key("wrong-key" * 4) is False

    def test_legacy_row_rehashes_on_success(self, legacy_api_key):
        from dbmail.models import ApiKey

        assert legacy_api_key.password_hash == ""
        assert legacy_api_key.is_valid_key("y" * 32) is True
        legacy_api_key.refresh_from_db()
        assert legacy_api_key.password_hash != ""
        # Subsequent call goes through the hashed path.
        fresh = ApiKey.objects.get(pk=legacy_api_key.pk)
        assert fresh.is_valid_key("y" * 32) is True

    def test_legacy_row_with_wrong_key_rejected(self, legacy_api_key):
        assert legacy_api_key.is_valid_key("wrong" * 7) is False
        legacy_api_key.refresh_from_db()
        # Failed match must NOT populate password_hash.
        assert legacy_api_key.password_hash == ""


class TestApiKeyMarkUsed:
    def test_mark_used_sets_timestamp_and_ip(self, api_key):
        from dbmail.models import ApiKey

        assert api_key.last_used_at is None
        api_key.mark_used("203.0.113.5")
        fresh = ApiKey.objects.get(pk=api_key.pk)
        assert fresh.last_used_at is not None
        assert fresh.last_used_ip == "203.0.113.5"

    def test_mark_used_with_none_ip(self, api_key):
        from dbmail.models import ApiKey

        api_key.mark_used(None)
        fresh = ApiKey.objects.get(pk=api_key.pk)
        assert fresh.last_used_at is not None
        assert fresh.last_used_ip is None


# ---------------------------------------------------------------------------
# SignalDeferredDispatch JSON dual-write (pickle → JSON migration, step 1)
# ---------------------------------------------------------------------------


class TestToJsonOrNone:
    @pytest.mark.parametrize(
        "payload",
        [
            None,
            42,
            "string",
            [1, 2, 3],
            {"key": "value"},
            {"nested": {"deep": [1, 2, 3]}},
        ],
    )
    def test_json_friendly_passes(self, payload):
        from dbmail.models import SignalDeferredDispatch

        assert SignalDeferredDispatch._to_json_or_none(payload) == payload

    def test_django_friendly_extras_pass(self):
        # DjangoJSONEncoder handles datetime / UUID / Decimal.
        import datetime
        import decimal
        import uuid

        from dbmail.models import SignalDeferredDispatch

        for payload in (
            datetime.datetime(2026, 1, 1, 12, 0, 0),
            uuid.uuid4(),
            decimal.Decimal("3.14"),
        ):
            assert SignalDeferredDispatch._to_json_or_none(payload) is not None

    def test_model_class_returns_none(self):
        from dbmail.models import ApiKey, SignalDeferredDispatch

        assert SignalDeferredDispatch._to_json_or_none([ApiKey]) is None

    def test_set_returns_none(self):
        from dbmail.models import SignalDeferredDispatch

        assert SignalDeferredDispatch._to_json_or_none({1, 2, 3}) is None


class TestSignalDeferredDispatchAddTask:
    def test_add_task_dual_writes_json_friendly(self):
        from dbmail.models import SignalDeferredDispatch

        row = SignalDeferredDispatch.add_task(
            args=[1, 2],
            kwargs={"a": "b"},
            params={"queue": "default"},
            interval=10,
        )
        row.refresh_from_db()
        assert row.args_json == [1, 2]
        assert row.kwargs_json == {"a": "b"}
        assert row.params_json == {"queue": "default"}
        # And pickle blobs are populated too.
        assert row.args
        assert row.kwargs
        assert row.params

    def test_add_task_with_model_class_falls_back_to_pickle(self, caplog):
        import logging

        from dbmail.models import ApiKey, SignalDeferredDispatch

        with caplog.at_level(logging.WARNING, logger="dbmail.models"):
            row = SignalDeferredDispatch.add_task(
                args=[ApiKey],
                kwargs={},
                params={},
                interval=5,
            )
        row.refresh_from_db()
        assert row.args_json is None
        # kwargs_json and params_json are JSON-friendly empties; only
        # args_json gets None.
        assert row.kwargs_json == {}
        assert row.params_json == {}
        assert any("not JSON-serializable" in record.message for record in caplog.records)


class TestSignalDeferredDispatchLoadField:
    def test_load_field_prefers_json(self):
        from dbmail.models import SignalDeferredDispatch

        sdd = SignalDeferredDispatch()
        assert sdd._load_field([1, 2], b"<garbage>") == [1, 2]

    def test_load_field_falls_back_to_pickle_when_allowed(self, settings):
        import pickle

        from dbmail.models import SignalDeferredDispatch

        settings.DB_MAILER_ALLOW_PICKLE_LEGACY = True
        sdd = SignalDeferredDispatch()
        blob = pickle.dumps([99, 100])
        assert sdd._load_field(None, blob) == [99, 100]

    def test_load_field_pickle_blocked_by_default(self, settings):
        """Security: legacy pickle path is OFF by default (opt-in via DB_MAILER_ALLOW_PICKLE_LEGACY)."""
        import pickle

        import pytest

        from dbmail.models import SignalDeferredDispatch

        settings.DB_MAILER_ALLOW_PICKLE_LEGACY = False
        sdd = SignalDeferredDispatch()
        blob = pickle.dumps([99, 100])
        with pytest.raises(RuntimeError, match="legacy pickle"):
            sdd._load_field(None, blob)
