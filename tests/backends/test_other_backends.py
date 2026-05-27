from __future__ import annotations

from unittest import mock

import pytest

from dbmail.backends.bot import Sender as BotSender
from dbmail.backends.bot import SenderDebug as BotDebug
from dbmail.backends.push import Sender as PushSender
from dbmail.backends.push import SenderDebug as PushDebug
from dbmail.backends.sms import Sender as SmsSender
from dbmail.backends.sms import SenderDebug as SmsDebug
from dbmail.backends.tts import Sender as TtsSender
from dbmail.backends.tts import SenderDebug as TtsDebug
from dbmail.models import (
    MailFromEmail,
    MailGroup,
    MailGroupEmail,
    MailTemplate,
)

pytestmark = pytest.mark.django_db


@pytest.fixture
def from_email(db):
    return MailFromEmail.objects.create(name="Sender", email="+19998887766")


def _tpl(slug, from_email, *, html=False):
    return MailTemplate.objects.create(
        name=slug,
        subject="Subj {{ name }}",
        from_email=from_email,
        message="Body {{ name }}",
        slug=slug,
        is_html=html,
    )


@pytest.fixture
def sms_tpl(from_email):
    return _tpl("test-sms", from_email)


@pytest.fixture
def push_tpl(from_email):
    return _tpl("test-push", from_email)


@pytest.fixture
def tts_tpl(from_email):
    return _tpl("test-tts", from_email)


@pytest.fixture
def bot_tpl(from_email):
    return _tpl("test-bot", from_email)


def _send(cls, slug, recipient, **kw):
    kw.setdefault("backend", "sms")
    return cls(slug, recipient, {"name": "Bob"}, **kw)


def test_sms_sender_phone_recipient_kept(sms_tpl):
    sender = _send(SmsSender, "test-sms", "+15554443322")
    assert sender._recipient_list == ["+15554443322"]


def test_sms_sender_group_lookup(sms_tpl, db):
    grp = MailGroup.objects.create(name="phones", slug="sms-grp")
    MailGroupEmail.objects.create(group=grp, email="+15550009999", name="m")
    sender = _send(SmsSender, "test-sms", "sms-grp")
    assert sender._recipient_list == ["+15550009999"]


def test_sms_send_calls_provider(sms_tpl):
    sender = _send(SmsSender, "test-sms", "+15554443322")
    fake = mock.MagicMock()
    with mock.patch("dbmail.backends.sms.import_module", return_value=fake):
        sender._send()
    fake.send.assert_called_once()
    args, kwargs = fake.send.call_args
    assert args[0] == "+15554443322"
    assert "Body Bob" in args[1]
    assert kwargs["sms_from"] == "+19998887766"


def test_sms_send_without_from(db, sms_tpl):
    sms_tpl.from_email = None
    sms_tpl.save()
    from django.core.cache import cache

    cache.clear()
    sender = _send(SmsSender, "test-sms", "+15554443322")
    sender._from_email = None
    fake = mock.MagicMock()
    with mock.patch("dbmail.backends.sms.import_module", return_value=fake):
        sender._send()
    args, kwargs = fake.send.call_args
    assert "sms_from" not in kwargs


def test_sms_get_from_email_kwargs_override(sms_tpl):
    sender = _send(SmsSender, "test-sms", "+15554443322", from_email="+13334445555")
    assert sender._from_email == "+13334445555"


def test_sms_get_from_email_no_template_uses_default_setting(db, settings):
    fe = MailFromEmail.objects.create(name="x", email="+10000000000")
    tpl = _tpl("sms-no-from", fe)
    tpl.from_email = None
    tpl.save()
    from django.core.cache import cache

    cache.clear()
    settings.DEFAULT_FROM_EMAIL = "ops <ops@example.com>"
    sender = _send(SmsSender, "sms-no-from", "+15554443322")
    assert sender._from_email == "ops"


def test_sms_get_from_email_with_default_sms_from(db, sms_tpl):
    sms_tpl.from_email = None
    sms_tpl.save()
    from django.core.cache import cache

    cache.clear()
    with mock.patch.object(SmsSender, "default_from", "+12222222222"):
        sender = _send(SmsSender, "test-sms", "+15554443322")
        assert sender._from_email == "+12222222222"


def test_sms_debug_writes_lines(sms_tpl, capsys):
    sender = SmsDebug("test-sms", "+15554443322", {"name": "Bob"}, backend="sms")
    sender._send()
    out = capsys.readouterr().out
    assert "Provider" in out
    assert "+15554443322" in out


def test_push_sender_token_recipient(push_tpl):
    sender = _send(PushSender, "test-push", ["device-token-1", "device-token-2"])
    assert sender._recipient_list == ["device-token-1", "device-token-2"]


def test_push_sender_group_lookup(db, push_tpl):
    grp = MailGroup.objects.create(name="devices", slug="push-grp")
    MailGroupEmail.objects.create(group=grp, email="device-tok", name="d")
    sender = _send(PushSender, "test-push", "push-grp")
    assert sender._recipient_list == ["device-tok"]


def test_push_sender_string_no_group_falls_through(push_tpl):
    sender = _send(PushSender, "test-push", "raw-token")
    assert sender._recipient_list == ["raw-token"]


def test_push_send_calls_provider_per_token(push_tpl):
    sender = _send(PushSender, "test-push", ["tok-a", "tok-b"])
    fake = mock.MagicMock()
    with mock.patch("dbmail.backends.push.import_module", return_value=fake):
        sender._send()
    assert fake.send.call_count == 2
    first_call = fake.send.call_args_list[0]
    assert first_call.args == ("tok-a",)
    assert first_call.kwargs["app"] == "+19998887766"


def test_push_send_uses_event_from_kwargs(push_tpl):
    sender = _send(PushSender, "test-push", ["tok-a"], event="custom-event")
    fake = mock.MagicMock()
    with mock.patch("dbmail.backends.push.import_module", return_value=fake):
        sender._send()
    assert fake.send.call_args.kwargs["event"] == "custom-event"


def test_push_send_event_defaults_to_subject(push_tpl):
    sender = _send(PushSender, "test-push", ["tok-a"])
    fake = mock.MagicMock()
    with mock.patch("dbmail.backends.push.import_module", return_value=fake):
        sender._send()
    assert fake.send.call_args.kwargs["event"] == "Subj Bob"


def test_push_debug_writes_lines(push_tpl, capsys):
    sender = PushDebug("test-push", ["tok-a"], {"name": "Bob"}, backend="push")
    sender._send()
    out = capsys.readouterr().out
    assert "Provider" in out
    assert "tok-a" in out


def test_tts_sender_uses_tts_provider(tts_tpl):
    from dbmail.defaults import TTS_PROVIDER

    sender = _send(TtsSender, "test-tts", "+15554443322")
    assert sender._provider == TTS_PROVIDER


def test_tts_send_invokes_provider(tts_tpl):
    sender = _send(TtsSender, "test-tts", "+15554443322")
    fake = mock.MagicMock()
    with mock.patch("dbmail.backends.sms.import_module", return_value=fake):
        sender._send()
    fake.send.assert_called_once()


def test_tts_debug_send(tts_tpl, capsys):
    sender = TtsDebug("test-tts", "+15554443322", {"name": "Bob"}, backend="tts")
    sender._send()
    assert "Provider" in capsys.readouterr().out


def test_bot_sender_recipient_list_passthrough(bot_tpl):
    sender = _send(BotSender, "test-bot", "12345,67890")
    assert sender._recipient_list == ["12345", "67890"]


def test_bot_send_invokes_provider(bot_tpl):
    sender = _send(BotSender, "test-bot", "12345")
    fake = mock.MagicMock()
    with mock.patch("dbmail.backends.bot.import_module", return_value=fake):
        sender._send()
    fake.send.assert_called_once()
    args, kwargs = fake.send.call_args
    assert args[0] == "12345"
    assert "Body Bob" in args[1]
    assert kwargs["_from"] == "+19998887766"


def test_bot_debug_inherits_sms_debug(bot_tpl):
    assert issubclass(BotDebug, SmsDebug)
