"""Tests for ``dbmail.providers._compat`` — shared provider helpers."""

from __future__ import annotations

import warnings

import pytest

from dbmail.providers._compat import from_unicode


class TestFromUnicode:
    """`from_unicode` returns ``str`` (3.0): provider payloads are JSON
    or form-data, where ``bytes`` would break ``json.dumps`` / urlencode."""

    def test_none_returns_empty_str(self):
        assert from_unicode(None) == ""

    def test_str_returns_str(self):
        assert from_unicode("hello") == "hello"
        assert from_unicode("привет") == "привет"

    def test_bytes_decoded_to_str(self):
        assert from_unicode(b"already bytes") == "already bytes"

    def test_truncate_by_utf8_byte_length(self):
        assert from_unicode("abcdef", text_length=3) == "abc"

    def test_truncate_drops_partial_multibyte(self):
        # 3 bytes of "привет" lands mid-cyrillic-codepoint; the
        # `errors='ignore'` decode drops the partial char.
        result = from_unicode("привет", text_length=3)
        # one full cyrillic codepoint = 2 bytes -> "п" only
        assert result == "п"

    def test_legacy_reexport_warns(self):
        # Importing the helper from prowl still works (back-compat) but
        # emits DeprecationWarning.
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            from dbmail.providers.prowl.push import from_unicode as legacy

            result = legacy("hi")
            assert result == "hi"
            assert any(issubclass(w.category, DeprecationWarning) for w in caught)


class TestProviderImports:
    """Smoke import for every shipped provider — must work without SDKs."""

    @pytest.mark.parametrize(
        "module",
        [
            "dbmail.providers.apple.apns",
            "dbmail.providers.apple.apns2",
            "dbmail.providers.apple.errors",
            "dbmail.providers.boxcar.push",
            "dbmail.providers.centrifugo.push",
            "dbmail.providers.google.android",
            "dbmail.providers.http.push",
            "dbmail.providers.iqsms.sms",
            "dbmail.providers.microsoft.base",
            "dbmail.providers.microsoft.raw",
            "dbmail.providers.microsoft.tile",
            "dbmail.providers.microsoft.toast",
            "dbmail.providers.nexmo.sms",
            "dbmail.providers.nexmo.tts",
            "dbmail.providers.parse_com.push",
            "dbmail.providers.prowl.push",
            "dbmail.providers.pushall.push",
            "dbmail.providers.pushover.push",
            "dbmail.providers.slack.push",
            "dbmail.providers.smsaero.sms",
            "dbmail.providers.smsbliss.sms",
            "dbmail.providers.telegram.bot",
            "dbmail.providers.twilio.sms",
        ],
    )
    def test_provider_import(self, module):
        import importlib

        importlib.import_module(module)
