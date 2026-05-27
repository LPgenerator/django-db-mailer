"""Tests for provider-level security and deprecation behaviour."""

from __future__ import annotations

import pytest

# ---------------------------------------------------------------------------
# EOL provider DeprecationWarning
# ---------------------------------------------------------------------------


class TestEOLDeprecationWarnings:
    """Each EOL provider emits ``DeprecationWarning`` on first ``send()``.

    We patch out the actual network call — we only care that the
    warning is emitted before any I/O happens.
    """

    def test_parse_com_warns(self, mocker):
        from dbmail.providers.parse_com import push

        mocker.patch.object(push, "HTTPSConnection")
        with pytest.warns(DeprecationWarning, match="parse_com"):
            try:
                push.send("dev_id", "msg", api_key="x")
            except Exception:
                pass

    def test_boxcar_warns(self, mocker):
        from dbmail.providers.boxcar import push

        mocker.patch.object(push, "HTTPSConnection")
        with pytest.warns(DeprecationWarning, match="boxcar"):
            try:
                push.send("token", "title", access_token="x")
            except Exception:
                pass

    def test_prowl_warns(self, mocker, settings):
        from dbmail.providers.prowl import push

        settings.PROWL_APP = "test"
        mocker.patch.object(push, "HTTPSConnection")
        with pytest.warns(DeprecationWarning, match="prowl"):
            try:
                push.send("apikey", "description", priority=1)
            except Exception:
                pass


# ---------------------------------------------------------------------------
# SSRF guard in http/push.py
# ---------------------------------------------------------------------------


class TestSSRF:
    def test_https_required_by_default(self, settings):
        from dbmail.providers.http.push import HTTPError, _check_url

        settings.DBMAIL_HTTP_ALLOW_INSECURE = False
        with pytest.raises(HTTPError, match="only https"):
            _check_url("http://example.com/hook")

    def test_http_allowed_with_explicit_setting(self, settings, mocker):
        from dbmail.providers.http import push

        settings.DBMAIL_HTTP_ALLOW_INSECURE = True
        # Stub DNS resolution to a public IP.
        mocker.patch.object(push, "_resolve_or_raise", return_value=None)
        scheme, netloc, port = push._check_url("http://example.com/hook")
        assert scheme == "http"
        assert port == 80

    def test_blocks_loopback(self, settings):
        from dbmail.providers.http.push import HTTPError, _check_url

        settings.DBMAIL_HTTP_ALLOW_INSECURE = True
        with pytest.raises(HTTPError, match="private"):
            _check_url("http://127.0.0.1/hook")

    def test_blocks_rfc1918(self, settings):
        from dbmail.providers.http.push import HTTPError, _check_url

        settings.DBMAIL_HTTP_ALLOW_INSECURE = True
        with pytest.raises(HTTPError, match="private"):
            _check_url("http://192.168.1.1/hook")

    def test_blocks_link_local(self, settings):
        from dbmail.providers.http.push import HTTPError, _check_url

        settings.DBMAIL_HTTP_ALLOW_INSECURE = True
        with pytest.raises(HTTPError, match="private"):
            _check_url("http://169.254.169.254/latest/")

    def test_blocks_cgnat(self, settings):
        from dbmail.providers.http.push import HTTPError, _check_url

        settings.DBMAIL_HTTP_ALLOW_INSECURE = True
        with pytest.raises(HTTPError, match="private"):
            _check_url("http://100.64.0.1/hook")

    def test_allowed_hosts_allowlist(self, settings, mocker):
        from dbmail.providers.http import push

        settings.DBMAIL_HTTP_ALLOWED_HOSTS = {"hooks.example.com"}
        mocker.patch.object(push, "_resolve_or_raise", return_value=None)

        # Listed host passes.
        push._check_url("https://hooks.example.com/x")
        # Unlisted host blocked even with valid scheme.
        with pytest.raises(push.HTTPError, match="not in DBMAIL_HTTP_ALLOWED_HOSTS"):
            push._check_url("https://other.example.com/x")

    def test_malformed_url_rejected(self, settings):
        from dbmail.providers.http.push import HTTPError, _check_url

        with pytest.raises(HTTPError, match="malformed"):
            _check_url("not-a-url")
