"""Per-provider send() tests using mocked HTTP layers.

Each provider gets a minimal happy-path or DeprecationWarning test.
Deeper failure-mode tests with full settings setup are scheduled for 3.1.0.
"""

from __future__ import annotations

import pytest


def _patch_https(mocker, module, status=200):
    """Stub HTTPSConnection / HTTPConnection on a module."""
    fake_response = mocker.Mock(status=status, reason="OK")
    fake_response.read.return_value = b'{"ok": true}'
    fake_conn = mocker.Mock()
    fake_conn.getresponse.return_value = fake_response
    fake_factory = mocker.Mock(return_value=fake_conn)
    if hasattr(module, "HTTPSConnection"):
        mocker.patch.object(module, "HTTPSConnection", fake_factory)
    if hasattr(module, "HTTPConnection"):
        mocker.patch.object(module, "HTTPConnection", fake_factory)
    return fake_conn, fake_response


def _patch_urlopen(mocker, module, status=200, body=b'{"ok": true}'):
    fake = mocker.MagicMock(code=status, status=status)
    fake.read.return_value = body
    fake.__enter__ = lambda self: self
    fake.__exit__ = lambda self, *exc: False
    return mocker.patch.object(module, "urlopen", return_value=fake)


# ---------------------------------------------------------------------------
# EOL providers — DeprecationWarning emitted before any I/O
# ---------------------------------------------------------------------------


class TestParseComProviderEmitsWarning:
    def test_warning_emitted_before_network(self, mocker, settings):
        from dbmail.providers.parse_com import push

        settings.PARSE_COM_APPLICATION_ID = "app"
        settings.PARSE_COM_REST_API_KEY = "key"
        _patch_https(mocker, push)
        with pytest.warns(DeprecationWarning):
            try:
                push.send("dev", "msg")
            except Exception:
                pass


class TestBoxcarProviderEmitsWarning:
    def test_warning_emitted_before_network(self, mocker):
        from dbmail.providers.boxcar import push

        _patch_https(mocker, push)
        with pytest.warns(DeprecationWarning):
            try:
                push.send("token", "title")
            except Exception:
                pass


# ---------------------------------------------------------------------------
# Pushall — uses urlopen, simple settings dict
# ---------------------------------------------------------------------------


class TestPushallProvider:
    def test_send_invokes_urlopen(self, mocker, settings):
        from dbmail.providers.pushall import push

        settings.PUSHALL_API_KEYS = {"ch": {"id": "1", "key": "k", "title": "T", "priority": "0"}}
        urlopen = _patch_urlopen(mocker, push, status=200, body=b'{"success":1}')
        result = push.send("ch", "msg")
        assert result is True
        assert urlopen.called


# ---------------------------------------------------------------------------
# HTTP webhook with SSRF guard
# ---------------------------------------------------------------------------


class TestHttpProviderHappyPath:
    def test_send_calls_https_after_check_url(self, mocker, settings):
        from dbmail.providers.http import push

        # Bypass DNS check (resolver would reject example.com in CI).
        mocker.patch.object(push, "_resolve_or_raise", return_value=None)
        conn, _ = _patch_https(mocker, push)

        result = push.send("https://hooks.example.com/webhook", "msg")
        assert result is True
        assert conn.request.called
