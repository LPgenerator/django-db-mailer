"""Tests for dbmail.views — API endpoint and security hardening."""

from __future__ import annotations

import hashlib
import hmac

import pytest
from django.test import RequestFactory

pytestmark = pytest.mark.django_db


# ---------------------------------------------------------------------------
# _client_ip
# ---------------------------------------------------------------------------


class TestClientIP:
    """`_client_ip` delegates to django-ipware. Tests verify the
    integration, not ipware's internal logic (it has its own suite)."""

    def setup_method(self):
        self.factory = RequestFactory()

    def test_returns_remote_addr_when_no_xff(self):
        from dbmail.views import _client_ip

        request = self.factory.post("/api/")
        request.META["REMOTE_ADDR"] = "198.51.100.7"
        assert _client_ip(request) == "198.51.100.7"

    def test_returns_xff_first_when_proxy_trusted(self, settings):
        # ipware honours IPWARE_TRUSTED_PROXY_LIST: when REMOTE_ADDR matches a
        # trusted proxy, the leftmost XFF entry wins.
        from dbmail.views import _client_ip

        settings.IPWARE_TRUSTED_PROXY_LIST = ["10.0.0.5"]
        request = self.factory.post("/api/")
        request.META["HTTP_X_FORWARDED_FOR"] = "1.2.3.4, 10.0.0.1"
        request.META["REMOTE_ADDR"] = "10.0.0.5"
        assert _client_ip(request) == "1.2.3.4"

    def test_returns_none_when_no_meta(self):
        from dbmail.views import _client_ip

        request = self.factory.post("/api/")
        request.META.pop("REMOTE_ADDR", None)
        assert _client_ip(request) is None

    def test_empty_xff_falls_back_to_remote_addr(self):
        from dbmail.views import _client_ip

        request = self.factory.post("/api/")
        request.META["HTTP_X_FORWARDED_FOR"] = ""
        request.META["REMOTE_ADDR"] = "198.51.100.7"
        assert _client_ip(request) == "198.51.100.7"


# ---------------------------------------------------------------------------
# _ratelimit_exceeded (cache-based sliding window)
# ---------------------------------------------------------------------------


class TestRateLimit:
    def test_disabled_when_count_zero(self, settings):
        from dbmail.views import _ratelimit_exceeded

        settings.DB_MAILER_API_RATE_LIMIT = (0, 60)
        for _ in range(10):
            assert _ratelimit_exceeded("api-key") is False

    def test_under_budget_returns_false(self, settings):
        from dbmail.views import _ratelimit_exceeded

        settings.DB_MAILER_API_RATE_LIMIT = (3, 60)
        assert _ratelimit_exceeded("k1") is False
        assert _ratelimit_exceeded("k1") is False
        assert _ratelimit_exceeded("k1") is False

    def test_over_budget_returns_true(self, settings):
        from dbmail.views import _ratelimit_exceeded

        settings.DB_MAILER_API_RATE_LIMIT = (3, 60)
        for _ in range(3):
            _ratelimit_exceeded("k2")
        assert _ratelimit_exceeded("k2") is True

    def test_per_key_isolation(self, settings):
        from dbmail.views import _ratelimit_exceeded

        settings.DB_MAILER_API_RATE_LIMIT = (2, 60)
        _ratelimit_exceeded("user-a")
        _ratelimit_exceeded("user-a")
        # user-a is now AT its budget; user-b is fresh.
        assert _ratelimit_exceeded("user-b") is False


# ---------------------------------------------------------------------------
# _hmac_check
# ---------------------------------------------------------------------------


class TestHmacCheck:
    def setup_method(self):
        self.factory = RequestFactory()

    def test_disabled_when_secret_empty(self, settings):
        from dbmail.views import _hmac_check

        settings.DB_MAILER_API_HMAC_SECRET = ""
        request = self.factory.post("/api/", data={"x": "y"})
        assert _hmac_check(request) is True

    def test_correct_signature_passes(self, settings):
        from dbmail.views import _hmac_check

        settings.DB_MAILER_API_HMAC_SECRET = "topsecret"
        body = b"slug=test&recipient=a@b.c"
        sig = hmac.new(b"topsecret", body, hashlib.sha256).hexdigest()
        request = self.factory.generic("POST", "/api/", data=body, content_type="application/x-www-form-urlencoded")
        request.META["HTTP_X_DBMAIL_SIGNATURE"] = "sha256=" + sig
        assert _hmac_check(request) is True

    def test_wrong_signature_fails(self, settings):
        from dbmail.views import _hmac_check

        settings.DB_MAILER_API_HMAC_SECRET = "topsecret"
        request = self.factory.generic("POST", "/api/", data=b"x=y", content_type="application/x-www-form-urlencoded")
        request.META["HTTP_X_DBMAIL_SIGNATURE"] = "sha256=" + "0" * 64
        assert _hmac_check(request) is False

    def test_missing_prefix_fails(self, settings):
        from dbmail.views import _hmac_check

        settings.DB_MAILER_API_HMAC_SECRET = "topsecret"
        request = self.factory.generic("POST", "/api/", data=b"x=y", content_type="application/x-www-form-urlencoded")
        request.META["HTTP_X_DBMAIL_SIGNATURE"] = "0" * 64
        assert _hmac_check(request) is False

    def test_missing_header_fails(self, settings):
        from dbmail.views import _hmac_check

        settings.DB_MAILER_API_HMAC_SECRET = "topsecret"
        request = self.factory.generic("POST", "/api/", data=b"x=y", content_type="application/x-www-form-urlencoded")
        assert _hmac_check(request) is False


# ---------------------------------------------------------------------------
# _safe_safari_push_path (path traversal)
# ---------------------------------------------------------------------------


class TestSafariPushPath:
    """``defaults.SAFARI_PUSH_PATH`` is a module-level constant resolved
    once at import time. Override via ``monkeypatch`` rather than the
    Django ``settings`` fixture.
    """

    def test_legitimate_site_pid_resolves_inside_base(self, monkeypatch, tmp_path):
        from dbmail import defaults
        from dbmail.views import _safe_safari_push_path

        monkeypatch.setattr(defaults, "SAFARI_PUSH_PATH", str(tmp_path))
        path = _safe_safari_push_path("example")
        assert path is not None
        assert path.startswith(str(tmp_path.resolve()))

    def test_traversal_dotdot_rejected(self, monkeypatch, tmp_path):
        from dbmail import defaults
        from dbmail.views import _safe_safari_push_path

        monkeypatch.setattr(defaults, "SAFARI_PUSH_PATH", str(tmp_path))
        assert _safe_safari_push_path("../../../etc/passwd") is None

    def test_traversal_with_leading_dot_rejected(self, monkeypatch, tmp_path):
        from dbmail import defaults
        from dbmail.views import _safe_safari_push_path

        monkeypatch.setattr(defaults, "SAFARI_PUSH_PATH", str(tmp_path))
        assert _safe_safari_push_path("../sibling") is None


# ---------------------------------------------------------------------------
# send_by_dbmail integration
# ---------------------------------------------------------------------------


class TestSendByDbmail:
    def setup_method(self):
        self.factory = RequestFactory()

    def test_get_returns_404(self, settings):
        from dbmail.views import send_by_dbmail

        request = self.factory.get("/api/")
        with pytest.raises(Exception):  # Http404
            send_by_dbmail(request)

    def test_missing_api_key_returns_404(self, settings):
        from dbmail.views import send_by_dbmail

        request = self.factory.post("/api/", data={"slug": "test"})
        with pytest.raises(Exception):
            send_by_dbmail(request)

    def test_invalid_api_key_returns_404(self, settings, db):
        from dbmail.views import send_by_dbmail

        request = self.factory.post("/api/", data={"api_key": "no-such-key", "slug": "test"})
        with pytest.raises(Exception):
            send_by_dbmail(request)

    def test_rate_limit_returns_429(self, settings, api_key):
        from dbmail.views import send_by_dbmail

        settings.DB_MAILER_API_RATE_LIMIT = (1, 60)
        # First call hits db (will 404 because no template), second hits 429.
        for _ in range(2):
            request = self.factory.post(
                "/api/",
                data={"api_key": api_key.api_key, "slug": "x", "recipient": "a@b.c"},
            )
            try:
                response = send_by_dbmail(request)
            except Exception:
                continue
            if response.status_code == 429:
                return
        pytest.fail("rate limit never returned 429")

    def test_hmac_mismatch_returns_403(self, settings, api_key):
        from dbmail.views import send_by_dbmail

        settings.DB_MAILER_API_HMAC_SECRET = "topsecret"
        request = self.factory.post(
            "/api/",
            data={"api_key": api_key.api_key, "slug": "x", "recipient": "a@b.c"},
        )
        request.META["HTTP_X_DBMAIL_SIGNATURE"] = "sha256=bad"
        response = send_by_dbmail(request)
        assert response.status_code == 403


# ---------------------------------------------------------------------------
# ApiKeyUsageAudit — persistent audit trail
# ---------------------------------------------------------------------------


class TestApiKeyUsageAudit:
    def setup_method(self):
        self.factory = RequestFactory()

    def test_audit_created_on_invalid_key(self, settings, db):
        from dbmail.models import ApiKeyUsageAudit
        from dbmail.views import send_by_dbmail

        request = self.factory.post(
            "/api/",
            data={"api_key": "z" * 32, "slug": "x", "recipient": "a@b.c"},
        )
        with pytest.raises(Exception):
            send_by_dbmail(request)
        rows = list(ApiKeyUsageAudit.objects.filter(action="invalid_key"))
        assert len(rows) == 1
        assert rows[0].success is False

    def test_audit_created_on_rate_limit(self, settings, api_key):
        from dbmail.models import ApiKeyUsageAudit
        from dbmail.views import send_by_dbmail

        settings.DB_MAILER_API_RATE_LIMIT = (1, 60)
        for _ in range(2):
            request = self.factory.post(
                "/api/",
                data={"api_key": api_key.api_key, "slug": "x", "recipient": "a@b.c"},
            )
            try:
                response = send_by_dbmail(request)
                if response.status_code == 429:
                    break
            except Exception:
                continue
        rows = list(ApiKeyUsageAudit.objects.filter(action="rate_limit"))
        assert len(rows) >= 1
        assert rows[0].success is False

    def test_audit_created_on_success(self, settings, api_key, monkeypatch):
        from dbmail import views as views_module
        from dbmail.models import ApiKeyUsageAudit
        from dbmail.views import send_by_dbmail

        # Stub db_sender so we don't need a real template wired up.
        monkeypatch.setattr(views_module, "db_sender", lambda *a, **kw: None)

        request = self.factory.post(
            "/api/",
            data={
                "api_key": api_key.api_key,
                "slug": "welcome",
                "recipient": "a@b.c",
            },
        )
        response = send_by_dbmail(request)
        assert response.status_code == 200
        rows = list(ApiKeyUsageAudit.objects.filter(action="send"))
        assert len(rows) == 1
        row = rows[0]
        assert row.success is True
        assert row.api_key_id == api_key.id
        assert row.api_key_name == api_key.name
        assert row.detail == "welcome"

    def test_audit_admin_is_readonly(self, db):
        from django.contrib import admin as django_admin

        from dbmail.admin import ApiKeyUsageAuditAdmin
        from dbmail.models import ApiKeyUsageAudit

        site = django_admin.AdminSite()
        admin_obj = ApiKeyUsageAuditAdmin(ApiKeyUsageAudit, site)
        assert admin_obj.has_add_permission(request=None) is False
        assert admin_obj.has_change_permission(request=None) is False
        # readonly_fields should cover every model field so the change-form
        # is effectively view-only when superuser opens an existing row.
        assert set(admin_obj.readonly_fields) == {f.name for f in ApiKeyUsageAudit._meta.fields}
