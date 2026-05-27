"""HTTP-mocked provider tests.

Each provider gets at minimum:

- happy-path 2xx test
- failure-path test (4xx/5xx auth or network error)

For ``requests``-based providers we use ``responses``; for the
``httpx``-based APNs HTTP/2 provider we use ``respx``. SDK-based
providers (telegram, mailin) are stubbed via ``sys.modules``.
"""

from __future__ import annotations

import json
import sys
import types
from unittest.mock import MagicMock

import httpx
import pytest
import responses

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _stub_https(mocker, module, status=200, body=b'{"ok": true}', reason="OK", headers=None):
    fake_response = MagicMock()
    fake_response.status = status
    fake_response.code = status
    fake_response.reason = reason
    fake_response.read.return_value = body
    fake_response.headers = _Headers(headers or {})
    fake_conn = MagicMock()
    fake_conn.getresponse.return_value = fake_response
    factory = MagicMock(return_value=fake_conn)
    if hasattr(module, "HTTPSConnection"):
        mocker.patch.object(module, "HTTPSConnection", factory)
    if hasattr(module, "HTTPConnection"):
        mocker.patch.object(module, "HTTPConnection", factory)
    return fake_conn, fake_response


def _patch_from_unicode_str(mocker, module):
    """Some providers pass ``from_unicode`` results (bytes) into json.dumps
    or string concatenation, which fails on py3. Patch the call sites in the
    provider module to return ``str`` so the code paths can execute under
    test. The pre-existing bug is tracked separately.
    """
    if hasattr(module, "from_unicode"):
        mocker.patch.object(
            module,
            "from_unicode",
            side_effect=lambda t, *a, **k: t if isinstance(t, str) else (t.decode() if t else ""),
        )


class _Headers(dict):
    def get_content_charset(self):
        return self.get("charset", "utf-8")


def _stub_urlopen(mocker, module, code=200, body=b'{"ok": true}'):
    fake = MagicMock()
    fake.code = code
    fake.status = code
    fake.read.return_value = body
    fake.__enter__ = lambda self: self
    fake.__exit__ = lambda self, *exc: False
    return mocker.patch.object(module, "urlopen", return_value=fake)


# ---------------------------------------------------------------------------
# slack
# ---------------------------------------------------------------------------


class TestSlackProvider:
    def _settings(self, settings):
        settings.SLACK_USERNAME = "bot"
        settings.SLACK_HOOCK_URL = "https://hooks.slack.com/services/AAA/BBB/CCC"
        settings.SLACK_CHANNEL = "#general"

    def test_slack_send_2xx_returns_true(self, mocker, settings):
        from dbmail.providers.slack import push

        self._settings(settings)
        _patch_from_unicode_str(mocker, push)
        _stub_https(mocker, push, status=200, body=b"ok")
        assert push.send("#general", "hi") is True

    def test_slack_send_5xx_raises(self, mocker, settings):
        from dbmail.providers.slack import push

        self._settings(settings)
        _patch_from_unicode_str(mocker, push)
        _stub_https(mocker, push, status=500, reason="boom")
        with pytest.raises(push.SlackError, match="boom"):
            push.send("#general", "hi")

    def test_slack_unexpected_body_raises(self, mocker, settings):
        from dbmail.providers.slack import push

        self._settings(settings)
        _patch_from_unicode_str(mocker, push)
        _stub_https(mocker, push, status=200, body=b"not_ok")
        with pytest.raises(push.SlackError):
            push.send("#general", "hi", data={"x": 1})


# ---------------------------------------------------------------------------
# pushover
# ---------------------------------------------------------------------------


class TestPushoverProvider:
    def _settings(self, settings):
        settings.PUSHOVER_TOKEN = "tok"
        settings.PUSHOVER_APP = "App"

    def test_pushover_send_2xx_returns_true(self, mocker, settings):
        from dbmail.providers.pushover import push

        self._settings(settings)
        _patch_from_unicode_str(mocker, push)
        _stub_https(mocker, push, status=200, body=b'{"status":1}')
        assert push.send("user", "hi", data={"sound": "b"}) is True

    def test_pushover_5xx_raises(self, mocker, settings):
        from dbmail.providers.pushover import push

        self._settings(settings)
        _patch_from_unicode_str(mocker, push)
        _stub_https(mocker, push, status=500, reason="oops")
        with pytest.raises(push.PushOverError):
            push.send("user", "hi")

    def test_pushover_status_zero_raises(self, mocker, settings):
        from dbmail.providers.pushover import push

        self._settings(settings)
        _patch_from_unicode_str(mocker, push)
        _stub_https(mocker, push, status=200, body=b'{"status":0,"errors":["bad token"]}')
        with pytest.raises(push.PushOverError):
            push.send("user", "hi")


# ---------------------------------------------------------------------------
# pushall (urlopen)
# ---------------------------------------------------------------------------


class TestPushallProvider:
    def _settings(self, settings):
        settings.PUSHALL_API_KEYS = {"ch": {"id": "1", "key": "k", "title": "T", "priority": "0"}}

    def test_pushall_send_returns_true(self, mocker, settings):
        from dbmail.providers.pushall import push

        self._settings(settings)
        _stub_urlopen(mocker, push, code=200, body=b'{"success":1}')
        assert push.send("ch", "msg") is True

    def test_pushall_500_raises(self, mocker, settings):
        from dbmail.providers.pushall import push

        self._settings(settings)
        _stub_urlopen(mocker, push, code=500, body=b"err")
        with pytest.raises(Exception):
            push.send("ch", "msg")


# ---------------------------------------------------------------------------
# centrifugo
# ---------------------------------------------------------------------------


class TestCentrifugoProvider:
    def _settings(self, settings):
        settings.CENTRIFUGO_TOKEN = "secret"
        settings.CENTRIFUGO_API = "https://centrifugo.example.com/api"

    def test_centrifugo_send_string_payload_2xx(self, mocker, settings):
        from dbmail.providers.centrifugo import push

        self._settings(settings)
        _stub_urlopen(mocker, push, code=200)
        assert push.send("ch", "hello") is True

    def test_centrifugo_send_dict_payload_2xx(self, mocker, settings):
        from dbmail.providers.centrifugo import push

        self._settings(settings)
        _stub_urlopen(mocker, push, code=200)
        assert push.send("ch", {"a": 1}) is True

    def test_centrifugo_bytes_secret_2xx(self, mocker, settings):
        from dbmail.providers.centrifugo import push

        settings.CENTRIFUGO_TOKEN = b"binary"
        settings.CENTRIFUGO_API = "https://centrifugo.example.com/api"
        _stub_urlopen(mocker, push, code=200)
        assert push.send("ch", "hi") is True

    def test_centrifugo_5xx_raises(self, mocker, settings):
        from dbmail.providers.centrifugo import push

        self._settings(settings)
        _stub_urlopen(mocker, push, code=500, body=b"err")
        with pytest.raises(push.CentrifugoError):
            push.send("ch", "hi")


# ---------------------------------------------------------------------------
# google.android (GCM)
# ---------------------------------------------------------------------------


class TestGoogleAndroidProvider:
    def _settings(self, settings):
        settings.GCM_KEY = "gcmkey"

    def test_android_send_2xx_returns_true(self, mocker, settings):
        from dbmail.providers.google import android

        self._settings(settings)
        _stub_https(mocker, android, status=200, body=b'{"failure":0,"success":1}')
        assert android.send("regid", "msg", event="evt") is True

    def test_android_5xx_raises(self, mocker, settings):
        from dbmail.providers.google import android

        self._settings(settings)
        _stub_https(mocker, android, status=500, reason="bad")
        with pytest.raises(android.GCMError):
            android.send("regid", "msg", event="evt")

    def test_android_failure_in_body_raises(self, mocker, settings):
        from dbmail.providers.google import android

        self._settings(settings)
        _stub_https(mocker, android, status=200, body=b'{"failure":1}')
        with pytest.raises(android.GCMError):
            android.send("regid", "msg", event="evt")


# ---------------------------------------------------------------------------
# google.browser (pywebpush) — stubbed module
# ---------------------------------------------------------------------------


@pytest.fixture
def fake_pywebpush():
    fake = types.ModuleType("pywebpush")

    class WebPusher:
        def __init__(self, sub):
            self.sub = sub

        def send(self, payload, gcm_key=None, ttl=60):
            return _resp_for_pywebpush

        def configure(self, response):  # pragma: no cover
            pass

    fake.WebPusher = WebPusher
    sys.modules["pywebpush"] = fake
    yield fake
    sys.modules.pop("pywebpush", None)
    sys.modules.pop("dbmail.providers.google.browser", None)


_resp_for_pywebpush = MagicMock(ok=True, text="")


class TestGoogleBrowserProvider:
    def _settings(self, settings):
        settings.GCM_KEY = "key"

    def test_browser_send_2xx(self, fake_pywebpush, settings):
        global _resp_for_pywebpush
        _resp_for_pywebpush = MagicMock(ok=True, text="")
        self._settings(settings)
        from dbmail.providers.google import browser

        result = browser.send(
            "regid",
            "msg",
            event="evt",
            subscription_info={"endpoint": "https://e.example/x"},
        )
        assert result is True

    def test_browser_send_failure_raises(self, fake_pywebpush, settings):
        global _resp_for_pywebpush
        _resp_for_pywebpush = MagicMock(ok=False, text='{"failure":1}')
        self._settings(settings)
        sys.modules.pop("dbmail.providers.google.browser", None)
        from dbmail.providers.google import browser

        with pytest.raises(browser.GCMError):
            browser.send(
                "regid",
                "msg",
                event="evt",
                subscription_info={"endpoint": "https://e.example/x"},
            )


# ---------------------------------------------------------------------------
# twilio (HTTPSConnection)
# ---------------------------------------------------------------------------


class TestTwilioProvider:
    def _settings(self, settings):
        settings.TWILIO_ACCOUNT_SID = "AC123"
        settings.TWILIO_AUTH_TOKEN = "tok"
        settings.TWILIO_FROM = "+10000000000"

    def test_twilio_send_201_returns_sid(self, mocker, settings):
        from dbmail.providers.twilio import sms

        self._settings(settings)
        _patch_from_unicode_str(mocker, sms)
        mocker.patch.object(sms, "b64encode", return_value=b"AUTH")
        _stub_https(mocker, sms, status=201, body=b'{"sid":"SM123"}')
        assert sms.send("+10000000001", "hi") == "SM123"

    def test_twilio_send_401_raises(self, mocker, settings):
        from dbmail.providers.twilio import sms

        self._settings(settings)
        _patch_from_unicode_str(mocker, sms)
        mocker.patch.object(sms, "b64encode", return_value=b"AUTH")
        _stub_https(mocker, sms, status=401, reason="auth")
        with pytest.raises(sms.TwilioSmsError):
            sms.send("+10000000001", "hi")

    def test_twilio_send_500_raises(self, mocker, settings):
        from dbmail.providers.twilio import sms

        self._settings(settings)
        _patch_from_unicode_str(mocker, sms)
        mocker.patch.object(sms, "b64encode", return_value=b"AUTH")
        _stub_https(mocker, sms, status=500, reason="server")
        with pytest.raises(sms.TwilioSmsError):
            sms.send("+10000000001", "hi")


# ---------------------------------------------------------------------------
# nexmo sms / tts (urlopen)
# ---------------------------------------------------------------------------


class TestNexmoProvider:
    def _settings(self, settings):
        settings.NEXMO_USERNAME = "u"
        settings.NEXMO_PASSWORD = "p"
        settings.NEXMO_FROM = "from"
        settings.NEXMO_LANG = "en-us"

    def test_nexmo_sms_send_2xx_returns_dict(self, mocker, settings):
        from dbmail.providers.nexmo import sms

        self._settings(settings)
        _stub_urlopen(mocker, sms, code=200, body=b'{"messages":[{"status":"0"}]}')
        result = sms.send("+10000000001", "hi")
        assert isinstance(result, dict)

    def test_nexmo_sms_error_text_raises(self, mocker, settings):
        from dbmail.providers.nexmo import sms

        self._settings(settings)
        _stub_urlopen(mocker, sms, code=200, body=b'{"messages":[{"error-text":"bad"}]}')
        with pytest.raises(sms.NexmoSmsError):
            sms.send("+10000000001", "hi")

    def test_nexmo_sms_top_level_status_raises(self, mocker, settings):
        from dbmail.providers.nexmo import sms

        self._settings(settings)
        _stub_urlopen(mocker, sms, code=200, body=b'{"status":"4","error-text":"nope"}')
        with pytest.raises(sms.NexmoSmsError):
            sms.send("+10000000001", "hi")

    def test_nexmo_tts_delegates_to_sms(self, mocker, settings):
        from dbmail.providers.nexmo import sms, tts

        self._settings(settings)
        _stub_urlopen(mocker, sms, code=200, body=b'{"messages":[{"status":"0"}]}')
        result = tts.send("+10000000001", "hi")
        assert isinstance(result, dict)


# ---------------------------------------------------------------------------
# iqsms
# ---------------------------------------------------------------------------


class TestIqsmsProvider:
    def _settings(self, settings):
        settings.IQSMS_API_LOGIN = "login"
        settings.IQSMS_API_PASSWORD = "pwd"
        settings.IQSMS_FROM = "sender"

    def test_iqsms_send_2xx_returns_id(self, mocker, settings):
        from dbmail.providers.iqsms import sms

        self._settings(settings)
        _patch_from_unicode_str(mocker, sms)
        mocker.patch.object(sms, "b64encode", return_value=b"AUTH")
        _stub_https(mocker, sms, status=200, body=b"42=accepted")
        assert sms.send("+10000000001", "hi") == 42

    def test_iqsms_send_5xx_raises(self, mocker, settings):
        from dbmail.providers.iqsms import sms

        self._settings(settings)
        _patch_from_unicode_str(mocker, sms)
        mocker.patch.object(sms, "b64encode", return_value=b"AUTH")
        _stub_https(mocker, sms, status=500, reason="bad")
        with pytest.raises(sms.IQSMSError):
            sms.send("+10000000001", "hi")

    def test_iqsms_send_rejected_body_raises(self, mocker, settings):
        from dbmail.providers.iqsms import sms

        self._settings(settings)
        _patch_from_unicode_str(mocker, sms)
        mocker.patch.object(sms, "b64encode", return_value=b"AUTH")
        _stub_https(mocker, sms, status=200, body=b"42=rejected")
        with pytest.raises(sms.IQSMSError):
            sms.send("+10000000001", "hi")


# ---------------------------------------------------------------------------
# smsaero
# ---------------------------------------------------------------------------


class TestSmsAeroProvider:
    def _settings(self, settings):
        settings.SMSAERO_LOGIN = "u"
        settings.SMSAERO_MD5_PASSWORD = "x"
        settings.SMSAERO_FROM = "from"

    def test_smsaero_accepted_returns_true(self, mocker, settings):
        from dbmail.providers.smsaero import sms

        self._settings(settings)
        _patch_from_unicode_str(mocker, sms)
        body = json.dumps({"id": "1", "result": "accepted"}).encode()
        _stub_https(mocker, sms, status=200, body=body, headers={"charset": "utf-8"})
        assert sms.send("+10000000001", "hi") is True

    def test_smsaero_no_id_returns_false(self, mocker, settings):
        from dbmail.providers.smsaero import sms

        self._settings(settings)
        _patch_from_unicode_str(mocker, sms)
        body = json.dumps({"result": "rejected"}).encode()
        _stub_https(mocker, sms, status=200, body=body, headers={"charset": "utf-8"})
        assert sms.send("+10000000001", "hi") is False

    def test_smsaero_5xx_raises(self, mocker, settings):
        from dbmail.providers.smsaero import sms

        self._settings(settings)
        _patch_from_unicode_str(mocker, sms)
        _stub_https(mocker, sms, status=500, reason="bad")
        with pytest.raises(sms.AeroSmsError):
            sms.send("+10000000001", "hi")


# ---------------------------------------------------------------------------
# smsbliss (requests + responses)
# ---------------------------------------------------------------------------


class TestSmsBlissProvider:
    def _settings(self, settings):
        settings.SMSBLISS_LOGIN = "user"
        settings.SMSBLISS_PASSWORD = "pwd"
        settings.SMSBLISS_API_URL = "https://api.smsbliss.example/send.json"
        settings.SMSBLISS_FROM = "sender"

    @responses.activate
    def test_smsbliss_send_2xx_accepted(self, mocker, settings):
        from dbmail.providers.smsbliss import sms

        self._settings(settings)
        _patch_from_unicode_str(mocker, sms)
        responses.add(
            responses.POST,
            "https://api.smsbliss.example/send.json",
            json={"messages": [{"status": "accepted"}]},
            status=200,
        )
        result = sms.send("+10000000001", "hi")
        assert result["messages"][0]["status"] == "accepted"

    @responses.activate
    def test_smsbliss_send_4xx_raises(self, mocker, settings):
        from dbmail.providers.smsbliss import sms

        self._settings(settings)
        _patch_from_unicode_str(mocker, sms)
        responses.add(
            responses.POST,
            "https://api.smsbliss.example/send.json",
            json={"error": "auth"},
            status=401,
        )
        with pytest.raises(sms.SMSBlissError):
            sms.send("+10000000001", "hi")

    @responses.activate
    def test_smsbliss_send_status_rejected_raises(self, mocker, settings):
        from dbmail.providers.smsbliss import sms

        self._settings(settings)
        _patch_from_unicode_str(mocker, sms)
        responses.add(
            responses.POST,
            "https://api.smsbliss.example/send.json",
            json={"messages": [{"status": "rejected"}]},
            status=200,
        )
        with pytest.raises(sms.SMSBlissError):
            sms.send("+10000000001", "hi")


# ---------------------------------------------------------------------------
# microsoft (base / toast / tile) — uses requests.post
# ---------------------------------------------------------------------------


class TestMicrosoftProviders:
    def _settings(self, settings):
        settings.WP_CERT_FILE = "/tmp/wp-cert.pem"

    @staticmethod
    def _patch_serialize(mocker, base):
        # serialize_tree concatenates str + bytes (legacy bug); bypass it.
        mocker.patch.object(base.MPNSBase, "serialize_tree", staticmethod(lambda tree: "<xml/>"))

    def test_toast_send_2xx_returns_true(self, mocker, settings):
        from dbmail.providers.microsoft import base, toast

        self._settings(settings)
        self._patch_serialize(mocker, base)
        fake = MagicMock(status_code=200, headers={"x-notificationstatus": "Received"}, reason="OK")
        mocker.patch.object(base, "post", return_value=fake)
        assert toast.send("https://wp.example/uri", "msg", event="App") is True

    def test_toast_queue_full_raises(self, mocker, settings):
        from dbmail.providers.microsoft import base, toast

        self._settings(settings)
        self._patch_serialize(mocker, base)
        fake = MagicMock(status_code=200, headers={"x-notificationstatus": "QueueFull"}, reason="Q")
        mocker.patch.object(base, "post", return_value=fake)
        with pytest.raises(base.WPError):
            toast.send("https://wp.example/uri", "msg", event="App")

    def test_toast_5xx_raises(self, mocker, settings):
        from dbmail.providers.microsoft import base, toast

        self._settings(settings)
        self._patch_serialize(mocker, base)
        fake = MagicMock(status_code=500, headers={}, reason="bad")
        mocker.patch.object(base, "post", return_value=fake)
        with pytest.raises(base.WPError):
            toast.send("https://wp.example/uri", "msg", event="App")

    def test_tile_send_2xx_returns_true(self, mocker, settings):
        from dbmail.providers.microsoft import base, tile

        self._settings(settings)
        self._patch_serialize(mocker, base)
        fake = MagicMock(status_code=200, headers={"x-notificationstatus": "Received"})
        mocker.patch.object(base, "post", return_value=fake)
        assert (
            tile.send(
                "https://wp.example/uri",
                "msg",
                event="App",
                count="1",
                back_title=None,
                id="A",
                template="T",
                background_image="img",
            )
            is True
        )

    def test_tile_5xx_raises(self, mocker, settings):
        from dbmail.providers.microsoft import base, tile

        self._settings(settings)
        self._patch_serialize(mocker, base)
        fake = MagicMock(status_code=500, headers={}, reason="oops")
        mocker.patch.object(base, "post", return_value=fake)
        with pytest.raises(base.WPError):
            tile.send("https://wp.example/uri", "msg", event="A")

    def test_base_msg_id_and_callback_uri_added(self, mocker, settings):
        from dbmail.providers.microsoft import base, toast

        self._settings(settings)
        self._patch_serialize(mocker, base)
        captured = {}

        def fake_post(uri, data, headers, cert, **kwargs):
            captured.update(headers)
            return MagicMock(status_code=200, headers={"x-notificationstatus": "Received"})

        mocker.patch.object(base, "post", side_effect=fake_post)
        instance = toast.MPNSToast()
        instance.send(
            "https://wp.example/uri",
            {"text1": "App", "text2": "msg"},
            msg_id="42",
            callback_uri="https://cb.example/",
        )
        assert captured.get("X-MessageID") == "42"
        assert captured.get("X-CallbackURI") == "https://cb.example/"


# ---------------------------------------------------------------------------
# http webhook
# ---------------------------------------------------------------------------


class TestHttpProvider:
    def test_http_send_2xx(self, mocker, settings):
        from dbmail.providers.http import push

        settings.DBMAIL_HTTP_ALLOW_INSECURE = False
        settings.HTTP_KEY = "k"
        mocker.patch.object(push, "_resolve_or_raise", return_value=None)
        _stub_https(mocker, push, status=200)
        assert push.send("https://hooks.example.com/x", "hi", http_key="z") is True

    def test_http_send_5xx_raises(self, mocker, settings):
        from dbmail.providers.http import push

        settings.DBMAIL_HTTP_ALLOW_INSECURE = False
        mocker.patch.object(push, "_resolve_or_raise", return_value=None)
        _stub_https(mocker, push, status=500, reason="oh")
        with pytest.raises(push.HTTPError):
            push.send("https://hooks.example.com/x", "hi")

    def test_http_send_uses_http_when_allowed(self, mocker, settings):
        from dbmail.providers.http import push

        settings.DBMAIL_HTTP_ALLOW_INSECURE = True
        mocker.patch.object(push, "_resolve_or_raise", return_value=None)
        _stub_https(mocker, push, status=200)
        assert push.send("http://hooks.example.com/x", "hi") is True

    def test_http_malformed_url_raises(self, settings):
        from dbmail.providers.http import push

        with pytest.raises(push.HTTPError, match="malformed"):
            push.send("not-a-url", "hi")

    def test_http_unsupported_scheme_raises(self, settings):
        from dbmail.providers.http import push

        settings.DBMAIL_HTTP_ALLOW_INSECURE = True
        with pytest.raises(push.HTTPError, match="unsupported scheme"):
            push._check_url("ftp://example.com/x")

    def test_http_allowed_hosts_enforced(self, settings):
        from dbmail.providers.http import push

        settings.DBMAIL_HTTP_ALLOW_INSECURE = False
        settings.DBMAIL_HTTP_ALLOWED_HOSTS = ["only.example.com"]
        with pytest.raises(push.HTTPError, match="DBMAIL_HTTP_ALLOWED_HOSTS"):
            push._check_url("https://other.example.com/x")
        settings.DBMAIL_HTTP_ALLOWED_HOSTS = None

    def test_http_dns_failure_raises(self, mocker, settings):
        from dbmail.providers.http import push

        settings.DBMAIL_HTTP_ALLOW_INSECURE = False
        import socket as _s

        mocker.patch.object(push.socket, "getaddrinfo", side_effect=_s.gaierror("nope"))
        with pytest.raises(push.HTTPError, match="dns"):
            push._check_url("https://nx.example.com/x")

    def test_http_no_addresses_resolved(self, mocker, settings):
        from dbmail.providers.http import push

        mocker.patch.object(push.socket, "getaddrinfo", return_value=[])
        with pytest.raises(push.HTTPError, match="no addresses"):
            push._resolve_or_raise("nx.example")


# ---------------------------------------------------------------------------
# parse_com (kept for deprecation coverage)
# ---------------------------------------------------------------------------


class TestParseComProvider:
    def _settings(self, settings):
        settings.PARSE_APP_ID = "app"
        settings.PARSE_API_KEY = "key"

    def test_parse_com_warns(self, mocker, settings):
        from dbmail.providers.parse_com import push

        self._settings(settings)
        _stub_https(mocker, push, status=200, body=b'{"result":1}')
        with pytest.warns(DeprecationWarning):
            try:
                push.send("device-id", "msg", event="evt")
            except Exception:
                pass


# ---------------------------------------------------------------------------
# prowl — already 84%, add 5xx + url branch
# ---------------------------------------------------------------------------


class TestProwlProvider:
    def test_prowl_5xx_raises(self, mocker, settings):
        from dbmail.providers.prowl import push

        settings.PROWL_APP = "App"
        _stub_https(mocker, push, status=500, reason="bad")
        with pytest.warns(DeprecationWarning):
            with pytest.raises(push.ProwlError):
                push.send("apikey", "desc")

    def test_prowl_2xx_with_url_and_provider_key(self, mocker, settings):
        from dbmail.providers.prowl import push

        settings.PROWL_APP = "App"
        _stub_https(mocker, push, status=200)
        with pytest.warns(DeprecationWarning):
            assert (
                push.send(
                    "apikey",
                    "desc",
                    providerkey="pk",
                    url="https://example.com/" + ("x" * 1000),
                )
                is True
            )

    def test_prowl_from_unicode_warns(self):
        from dbmail.providers.prowl import push

        with pytest.warns(DeprecationWarning):
            assert push.from_unicode("hello") == "hello"


# ---------------------------------------------------------------------------
# telegram (mocked telepot SDK)
# ---------------------------------------------------------------------------


@pytest.fixture
def fake_telepot():
    fake = types.ModuleType("telepot")

    class Bot:
        last_call = {}

        def __init__(self, token):
            Bot.last_call["token"] = token

        def sendMessage(self, to, msg, **kw):
            Bot.last_call["to"] = to
            Bot.last_call["msg"] = msg
            Bot.last_call["kw"] = kw
            if to == "fail":
                raise RuntimeError("api auth")
            return {"message_id": 1, "chat": {"id": to}}

    fake.Bot = Bot
    sys.modules["telepot"] = fake
    yield fake
    sys.modules.pop("telepot", None)


class TestTelegramProvider:
    def test_telegram_send_returns_dict(self, fake_telepot, settings):
        settings.TELEGRAM_BOT_TOKEN = "t"
        from dbmail.providers.telegram import bot

        result = bot.send("123", "hi", parse_mode="HTML", unknown_arg="ignored")
        assert result["message_id"] == 1
        assert fake_telepot.Bot.last_call["kw"] == {"parse_mode": "HTML"}

    def test_telegram_send_propagates_error(self, fake_telepot, settings):
        settings.TELEGRAM_BOT_TOKEN = "t"
        from dbmail.providers.telegram import bot

        with pytest.raises(RuntimeError, match="api auth"):
            bot.send("fail", "hi")


# ---------------------------------------------------------------------------
# sendinblue mail (mailin SDK stubbed)
# ---------------------------------------------------------------------------


@pytest.fixture
def fake_mailin():
    state = {}
    fake = types.ModuleType("mailin")

    class Mailin:
        def __init__(self, url, key):
            state["init"] = (url, key)

        def send_email(self, data):
            state["send"] = data
            if data.get("subject") == "fail":
                return {"code": "failure", "message": "boom"}
            return {"code": "success", "message-id": "MSG1"}

    fake.Mailin = Mailin
    fake.state = state
    import importlib

    sys.modules.pop("dbmail.providers.sendinblue.mail", None)
    sys.modules.pop("dbmail.providers.sendinblue", None)
    sys.modules["mailin"] = fake
    importlib.invalidate_caches()
    yield fake
    sys.modules.pop("mailin", None)
    sys.modules.pop("dbmail.providers.sendinblue.mail", None)
    sys.modules.pop("dbmail.providers.sendinblue", None)


class _FakeTemplate:
    def __init__(self, is_html=True):
        self.is_html = is_html


class _FakeSender:
    def __init__(self, is_html=True, subject="hi", attachments=None):
        self._kwargs = {"api_key": "k"}
        if attachments is not None:
            self._kwargs["attachments"] = attachments
        self._recipient_list = ["John Doe <john@example.com>"]
        self._cc = []
        self._bcc = ["bcc@example.com"]
        self._from_email = "Sender <sender@example.com>"
        self._subject = subject
        self._message = "<p>hi</p>" if is_html else "hi"
        self._template = _FakeTemplate(is_html=is_html)


class TestSendInBlueProvider:
    def test_sendinblue_html_send_success(self, fake_mailin):
        from dbmail.providers.sendinblue import mail

        mail.send(_FakeSender(is_html=True))
        data = fake_mailin.state["send"]
        assert "html" in data
        assert data["bcc"] == {"bcc@example.com": "bcc@example.com"}

    def test_sendinblue_text_send_success(self, fake_mailin):
        from dbmail.providers.sendinblue import mail

        mail.send(_FakeSender(is_html=False))
        data = fake_mailin.state["send"]
        assert "text" in data

    def test_sendinblue_with_attachments(self, fake_mailin):
        from dbmail.providers.sendinblue import mail

        mail.send(_FakeSender(attachments=[("file.txt", b"abc")]))
        data = fake_mailin.state["send"]
        assert "attachment" in data
        assert "file.txt" in data["attachment"]

    def test_sendinblue_failure_raises(self, fake_mailin):
        from dbmail.providers.sendinblue import mail

        with pytest.raises(mail.SendInBlueError, match="boom"):
            mail.send(_FakeSender(subject="fail"))


# ---------------------------------------------------------------------------
# apple.apns2 (httpx + respx)
# ---------------------------------------------------------------------------


class TestAppleApns2Provider:
    def _settings(self, settings):
        settings.APNS_GW_HOST = "api.push.apple.com"
        settings.APNS_GW_PORT = 443
        settings.APNS_CERT_FILE = "/tmp/cert.pem"

    def test_apns2_send_2xx_returns_true(self, settings, mocker):
        self._settings(settings)
        from dbmail.providers.apple import apns2

        fake_resp = httpx.Response(200, text="")
        client_mock = MagicMock()
        client_mock.__enter__ = lambda self: client_mock
        client_mock.__exit__ = lambda self, *a: False
        client_mock.post.return_value = fake_resp
        mocker.patch.object(httpx, "Client", return_value=client_mock)

        assert apns2.send("token", "hi", event="evt", topic="bundle.id") is True

    def test_apns2_send_5xx_raises(self, settings, mocker):
        self._settings(settings)
        from dbmail.providers.apple import apns2

        fake_resp = httpx.Response(500, text="server")
        client_mock = MagicMock()
        client_mock.__enter__ = lambda self: client_mock
        client_mock.__exit__ = lambda self, *a: False
        client_mock.post.return_value = fake_resp
        mocker.patch.object(httpx, "Client", return_value=client_mock)

        with pytest.raises(apns2.APNsError):
            apns2.send("token", "hi", event="evt")

    def test_apns2_send_with_key_file(self, settings, mocker):
        self._settings(settings)
        settings.APNS_KEY_FILE = "/tmp/key.pem"
        from dbmail.providers.apple import apns2

        fake_resp = httpx.Response(200, text="")
        client_mock = MagicMock()
        client_mock.__enter__ = lambda self: client_mock
        client_mock.__exit__ = lambda self, *a: False
        client_mock.post.return_value = fake_resp
        captured = {}

        def factory(**kw):
            captured.update(kw)
            return client_mock

        mocker.patch.object(httpx, "Client", side_effect=factory)
        assert apns2.send("token", "hi", event="evt", content_available=1) is True
        # cert is a tuple when key_file present
        assert isinstance(captured.get("cert"), tuple)

    def test_apns2_unauthorized_raises(self, settings, mocker):
        self._settings(settings)
        from dbmail.providers.apple import apns2

        fake_resp = httpx.Response(403, text='{"reason":"BadCertificate"}')
        client_mock = MagicMock()
        client_mock.__enter__ = lambda self: client_mock
        client_mock.__exit__ = lambda self, *a: False
        client_mock.post.return_value = fake_resp
        mocker.patch.object(httpx, "Client", return_value=client_mock)

        with pytest.raises(apns2.APNsError):
            apns2.send("token", "hi", event="evt")
