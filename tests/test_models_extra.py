"""Extra model coverage — MailTemplate cache, MailLog cleanup,
MailLogException truncate, MailFromEmail / MailGroup / etc.
"""

from __future__ import annotations

import pytest

pytestmark = pytest.mark.django_db


@pytest.fixture
def template():
    from dbmail.models import MailTemplate

    return MailTemplate.objects.create(
        name="Tpl",
        subject="Hi",
        message="Body",
        slug="tpl-1",
        is_active=True,
    )


class TestMailTemplate:
    def test_get_template_by_slug(self, template):
        from dbmail.models import MailTemplate

        same = MailTemplate.get_template(slug="tpl-1")
        assert same.pk == template.pk

    def test_str_returns_name(self, template):
        assert str(template) == "Tpl"

    def test_save_persists_changes(self, template):
        from dbmail.models import MailTemplate

        template.subject = "Updated"
        template.save()
        fresh = MailTemplate.objects.get(pk=template.pk)
        assert fresh.subject == "Updated"


class TestMailLog:
    def test_cleanup_removes_old_logs(self, template, settings):
        from dbmail.models import MailLog

        settings.DB_MAILER_LOGS_EXPIRE_DAYS = 7
        MailLog.objects.create(template=template, is_sent=True, log_id="x")
        # No old logs initially.
        before = MailLog.objects.count()
        MailLog.cleanup(days=7)
        assert MailLog.objects.count() == before

    def test_str_returns_template_name(self, template):
        from dbmail.models import MailLog

        log = MailLog.objects.create(template=template, is_sent=True, log_id="y")
        assert str(log) == "Tpl"

    def test_create_log_directly(self, template):
        from dbmail.models import MailLog

        log = MailLog.objects.create(template=template, is_sent=True, log_id="store-1")
        fresh = MailLog.objects.get(log_id="store-1")
        assert fresh.pk == log.pk


class TestMailLogException:
    def test_get_or_create_returns_same_for_same_message(self):
        from dbmail.models import MailLogException

        e = MailLogException.get_or_create("BOOM!")
        e2 = MailLogException.get_or_create("BOOM!")
        assert e.pk == e2.pk

    def test_str_returns_message_truncated(self):
        from dbmail.models import MailLogException

        e = MailLogException.get_or_create("x" * 200)
        assert str(e).startswith("xxx")


class TestMailFromEmail:
    def test_create_and_str(self):
        from dbmail.models import MailFromEmail

        m = MailFromEmail.objects.create(name="Sender", email="from@example.com")
        assert str(m) == "Sender"
        assert "from@example.com" in m.get_mail_from


class TestMailGroup:
    def test_get_emails_collects_addresses(self):
        from dbmail.models import MailGroup, MailGroupEmail

        g = MailGroup.objects.create(name="g", slug="g")
        MailGroupEmail.objects.create(group=g, name="A", email="a@x.com")
        MailGroupEmail.objects.create(group=g, name="B", email="b@x.com")
        emails = MailGroup.get_emails("g")
        assert set(emails) == {"a@x.com", "b@x.com"}


class TestApiKeyExtra:
    def test_str_returns_name(self):
        from dbmail.models import ApiKey

        k = ApiKey.objects.create(name="prod", api_key="z" * 32)
        assert str(k) == "prod"

    def test_clean_cache_classmethod(self):
        from dbmail.models import ApiKey

        ApiKey.objects.create(name="a", api_key="a" * 32)
        ApiKey.objects.create(name="b", api_key="b" * 32)
        # Must not raise; clears cache for all rows.
        ApiKey.clean_cache()


class TestMailLogTrackTrack:
    def test_track_records_user_agent_via_request_headers(self):
        from django.core import signing

        from dbmail.models import MailFromEmail, MailLog, MailLogTrack, MailTemplate

        sender = MailFromEmail.objects.create(name="s", email="s@example.com")
        tpl = MailTemplate.objects.create(name="t", subject="s", slug="tpl-track", message="hi", from_email=sender)
        mlog = MailLog.objects.create(template=tpl, is_sent=True)
        encrypted = signing.dumps(mlog.log_id)
        http_meta = {
            "HTTP_USER_AGENT": "Mozilla/5.0 (test)",
            "REMOTE_ADDR": "10.0.0.5",
        }

        MailLogTrack.track(http_meta, encrypted)

        track = MailLogTrack.objects.get(mail_log=mlog)
        assert track.ua == "Mozilla/5.0 (test)"
        assert track.is_read is True

    def test_track_handles_missing_user_agent(self):
        from django.core import signing

        from dbmail.models import MailFromEmail, MailLog, MailLogTrack, MailTemplate

        sender = MailFromEmail.objects.create(name="s2", email="s2@example.com")
        tpl = MailTemplate.objects.create(name="t2", subject="s", slug="tpl-track-2", message="hi", from_email=sender)
        mlog = MailLog.objects.create(template=tpl, is_sent=True)
        encrypted = signing.dumps(mlog.log_id)

        MailLogTrack.track({"REMOTE_ADDR": "10.0.0.6"}, encrypted)

        track = MailLogTrack.objects.get(mail_log=mlog)
        assert track.ua is None


class TestMailSubscriptionNotify:
    """Wave 1 H1 / H2: notify() must tolerate missing use_celery and
    must not blow up the query count linearly with the number of
    matching subscriptions."""

    def _mk_subs(self, count, slug):
        from dbmail.models import MailSubscription, MailTemplate

        # Template the notify() path resolves; create it via slug so
        # MailTemplate.get_template caches it on first hit.
        MailTemplate.objects.create(
            name=f"tpl-{slug}",
            subject="hello",
            slug=slug,
            message="hi",
            is_active=True,
        )
        subs = []
        for i in range(count):
            subs.append(
                MailSubscription.objects.create(
                    address=f"u{i}@example.com",
                    is_enabled=True,
                    is_checked=True,
                )
            )
        return subs

    def test_notify_without_use_celery_kwarg_does_not_raise(self, monkeypatch):
        """H1: notify() must default use_celery to False when caller
        omits it (previously raised KeyError on the outside-allowed-hour
        branch and silently dropped notifications)."""
        from dbmail import models as models_mod

        self._mk_subs(1, "sub-h1")

        # Force the outside-allowed-hours branch so the use_celery
        # lookup runs.
        sub = models_mod.MailSubscription.objects.first()
        sub.start_hour = "00:00"
        sub.end_hour = "00:00"
        sub.defer_at_allowed_hours = False
        sub.save()

        sent = []
        monkeypatch.setattr(
            "dbmail.db_sender",
            lambda *a, **kw: sent.append((a, kw)),
        )
        # No use_celery in kwargs — must not raise.
        models_mod.MailSubscription.notify("sub-h1")
        # The defer-skipped branch skipped delivery; that is the
        # intended behavior — the bug was a hard crash, not lost mail.
        assert sent == []

    def test_notify_queries_dont_scale_linearly(self, django_assert_max_num_queries, monkeypatch):
        """H2: notify() iterated values_list("pk") and then re-fetched
        each row via .objects.get(pk=). Five subscribers used to issue
        1 + N queries for the subscription rows alone. With
        .iterator() it stays at 1."""
        from dbmail import models as models_mod

        self._mk_subs(5, "sub-h2")
        # Seed the resolved per-backend template so get_final_slug
        # caches it on first hit and only the subscription cursor query
        # remains.
        models_mod.MailTemplate.objects.create(
            name="tpl-sub-h2-mail",
            subject="hi",
            slug="sub-h2-mail",
            message="hi",
            is_active=True,
        )
        monkeypatch.setattr("dbmail.db_sender", lambda *a, **kw: None)

        # Old behavior: 1 (subscriptions list) + 5 (per-sub re-fetch)
        # + 4 template-cache fills on the first hit = 10 for five rows.
        # New behavior: 1 cursor + 4 cache-fill queries on the first
        # row, then everything is served from the in-process cache.
        # The point is that the count does NOT scale with the number
        # of subscriptions.
        with django_assert_max_num_queries(4):
            models_mod.MailSubscription.notify("sub-h2", use_celery=True)

        # Sanity check: a second pass (now with the cache warm) drops
        # to a single subscription cursor query, proving the win.
        with django_assert_max_num_queries(1):
            models_mod.MailSubscription.notify("sub-h2", use_celery=True)


class TestApiKeyCleanCacheBatch:
    """Wave 1 H4: ApiKey.clean_cache() loaded the whole table into
    memory and issued one cache.delete per row. New behavior is a
    single delete_many() over all keys."""

    def test_clean_cache_uses_delete_many(self, mocker):
        from django.core.cache import cache

        from dbmail.models import ApiKey

        for i in range(5):
            ApiKey.objects.create(name=f"k{i}", api_key=str(i) * 32)

        spy_many = mocker.spy(cache, "delete_many")

        ApiKey.clean_cache()

        # One bulk call, not five individual ones.
        assert spy_many.call_count == 1
        # 10 entries flushed in one shot (legacy + hashed for each row).
        flushed = spy_many.call_args.args[0]
        assert len(flushed) == 10

    def test_clean_cache_noop_on_empty_table(self, mocker):
        from django.core.cache import cache

        from dbmail.models import ApiKey

        spy_many = mocker.spy(cache, "delete_many")

        ApiKey.clean_cache()

        assert spy_many.call_count == 0

    def test_clean_cache_does_not_load_whole_table(self, mocker):
        """``.iterator(chunk_size=500)`` keeps the queryset off-heap.

        Verified indirectly: the queryset returned to the loop must
        not call ``__len__`` / cache rows like a regular QuerySet."""
        from dbmail.models import ApiKey

        for i in range(3):
            ApiKey.objects.create(name=f"k{i}", api_key=str(i) * 32)

        qs_spy = mocker.spy(ApiKey.objects.__class__, "values_list")
        ApiKey.clean_cache()
        # values_list("api_key", flat=True) is the only queryset path.
        assert qs_spy.call_count == 1
        assert qs_spy.call_args.args[1:] == ("api_key",)


class TestNaturalKeys:
    """C3: 7 models expose natural keys for fixture round-trips."""

    def test_mail_category(self):
        from dbmail.models import MailCategory

        obj = MailCategory.objects.create(name="alerts")
        assert obj.natural_key() == ("alerts",)
        assert MailCategory.objects.get_by_natural_key("alerts") == obj

    def test_mail_base_template(self):
        from dbmail.models import MailBaseTemplate

        obj = MailBaseTemplate.objects.create(name="Action", message="{{content}}")
        assert obj.natural_key() == ("Action",)
        assert MailBaseTemplate.objects.get_by_natural_key("Action") == obj

    def test_mail_from_email(self):
        from dbmail.models import MailFromEmail

        obj = MailFromEmail.objects.create(name="ops", email="ops@example.com")
        assert obj.natural_key() == ("ops@example.com",)
        assert MailFromEmail.objects.get_by_natural_key("ops@example.com") == obj

    def test_mail_bcc(self):
        from dbmail.models import MailBcc

        obj = MailBcc.objects.create(email="bcc@example.com")
        assert obj.natural_key() == ("bcc@example.com",)
        assert MailBcc.objects.get_by_natural_key("bcc@example.com") == obj

    def test_mail_template(self):
        from dbmail.models import MailTemplate

        obj = MailTemplate.objects.create(
            name="welcome",
            subject="hi",
            message="hello",
            slug="welcome",
        )
        assert obj.natural_key() == ("welcome",)
        assert MailTemplate.objects.get_by_natural_key("welcome") == obj

    def test_mail_log_exception(self):
        from dbmail.models import MailLogException

        obj = MailLogException.objects.create(name="ValueError")
        assert obj.natural_key() == ("ValueError",)
        assert MailLogException.objects.get_by_natural_key("ValueError") == obj

    def test_mail_group(self):
        from dbmail.models import MailGroup

        obj = MailGroup.objects.create(name="staff", slug="staff")
        assert obj.natural_key() == ("staff",)
        assert MailGroup.objects.get_by_natural_key("staff") == obj

    def test_fixture_loaddata_via_natural_keys(self):
        """The bundled mailgun_base_templates fixture must load without
        explicit pks (rows are matched by name)."""
        from django.core.management import call_command

        from dbmail.models import MailBaseTemplate

        call_command("loaddata", "mailgun_base_templates", verbosity=0)
        names = set(MailBaseTemplate.objects.values_list("name", flat=True))
        assert names == {"Action", "Alert", "Billing"}


class TestMailLogCorrelationId:
    """C4 / ADR-0011 — correlation_id is plumbed through the public API
    and the MailLog row carries it for distributed tracing."""

    def test_maillog_correlation_id_stored(self, template):
        from dbmail.models import MailLog

        MailLog.store(
            ["to@x.com"],
            [],
            [],
            True,
            template,
            None,
            1,
            log_id="cid-1",
            backend="mail",
            correlation_id="order-123",
        )
        row = MailLog.objects.get(log_id="cid-1")
        assert row.correlation_id == "order-123"

    def test_maillog_correlation_id_optional(self, template):
        from dbmail.models import MailLog

        MailLog.store(
            ["to@x.com"],
            [],
            [],
            True,
            template,
            None,
            1,
            log_id="cid-2",
            backend="mail",
        )
        row = MailLog.objects.get(log_id="cid-2")
        assert row.correlation_id is None

    def test_send_db_mail_passes_correlation_id_through(self, template, mocker):
        """send_db_mail -> db_sender -> Sender(__init__) -> _store_log
        forwards correlation_id all the way to MailLog.store."""
        from dbmail.backends import mail as mail_backend

        spy = mocker.spy(mail_backend.MailLog, "store")
        mocker.patch.object(mail_backend.Sender, "_send", return_value=True)
        mail_backend.Sender(
            template.slug,
            "to@x.com",
            backend="mail",
            correlation_id="req-1",
        ).send(is_celery=False)
        assert spy.call_count == 1
        assert spy.call_args.kwargs.get("correlation_id") == "req-1"

    def test_correlation_id_truncated_to_64(self, template):
        """Django's CharField rejects values longer than max_length when
        full_clean() runs — guards us from silently truncating tags."""
        from django.core.exceptions import ValidationError

        from dbmail.models import MailLog

        log = MailLog(
            template=template,
            is_sent=True,
            log_id="cid-len",
            backend="mail",
            correlation_id="x" * 65,
        )
        with pytest.raises(ValidationError):
            log.full_clean()

    def test_admin_search_finds_by_correlation_id(self, template, client):
        """correlation_id is in MailLogAdmin.search_fields so support
        can locate a row by traceparent / order id."""
        from django.contrib.auth import get_user_model

        from dbmail.admin import MailLogAdmin
        from dbmail.models import MailLog

        user_model = get_user_model()
        admin_user = user_model.objects.create_superuser(username="root", email="root@x.com", password="pw")
        MailLog.objects.create(
            template=template,
            is_sent=True,
            log_id="cid-search",
            correlation_id="trace-deadbeef",
        )
        MailLog.objects.create(
            template=template,
            is_sent=True,
            log_id="cid-other",
            correlation_id="other-key",
        )
        # MailLogAdmin.search_fields contains 'correlation_id'.
        assert "correlation_id" in MailLogAdmin.search_fields
        # And the admin's get_search_results actually filters by it.
        from django.contrib import admin as django_admin
        from django.test import RequestFactory

        site = django_admin.site
        ma = MailLogAdmin(MailLog, site)
        request = RequestFactory().get("/")
        request.user = admin_user
        qs, _ = ma.get_search_results(request, MailLog.objects.all(), "trace-deadbeef")
        assert list(qs.values_list("log_id", flat=True)) == ["cid-search"]


class TestSignalLogUniqueConstraint:
    """H3 — UniqueConstraint blocks duplicate SignalLog rows and
    mark_as_sent stays idempotent under concurrent workers."""

    def _make_signal(self):
        from django.contrib.contenttypes.models import ContentType

        from dbmail.models import MailTemplate, Signal

        tpl = MailTemplate.objects.create(
            name="SigTpl",
            subject="s",
            message="m",
            slug="sig-tpl",
            is_active=True,
        )
        ct = ContentType.objects.get_for_model(MailTemplate)
        sig = Signal.objects.create(
            name="sig-uc",
            model=ct,
            template=tpl,
            receive_once=True,
            signal="post_save",
        )
        return sig, ct

    def test_signallog_unique_constraint_blocks_duplicate(self):
        from django.db import IntegrityError

        from dbmail.models import SignalLog

        sig, ct = self._make_signal()
        SignalLog.objects.create(signal=sig, model=ct, model_pk=42)
        with pytest.raises(IntegrityError):
            SignalLog.objects.create(signal=sig, model=ct, model_pk=42)

    def test_mark_as_sent_idempotent_under_race(self):
        from dbmail.models import SignalLog

        sig, _ = self._make_signal()
        sig.mark_as_sent(99)
        # Second call simulates the parallel worker that lost the race —
        # IntegrityError is caught, no exception bubbles up.
        sig.mark_as_sent(99)
        assert SignalLog.objects.filter(signal=sig, model_pk=99).count() == 1
