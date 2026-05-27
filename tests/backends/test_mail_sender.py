from __future__ import annotations

from smtplib import SMTPException
from unittest import mock

import pytest

from dbmail.backends.mail import Sender, SenderDebug
from dbmail.exceptions import StopSendingException
from dbmail.models import (
    MailFromEmail,
    MailFromEmailCredential,
    MailGroup,
    MailGroupEmail,
    MailLog,
    MailLogException,
    MailTemplate,
)

pytestmark = pytest.mark.django_db


@pytest.fixture
def from_email(db):
    return MailFromEmail.objects.create(name="Sender", email="sender@example.com")


@pytest.fixture
def template(db, from_email):
    return MailTemplate.objects.create(
        name="Hello",
        subject="Hello {{ name }}",
        from_email=from_email,
        message="Hi {{ name }}, body",
        slug="test-mail",
        is_html=False,
        is_active=True,
        enable_log=True,
    )


@pytest.fixture
def html_template(db, from_email):
    return MailTemplate.objects.create(
        name="HTMLHello",
        subject="HTML {{ name }}",
        from_email=from_email,
        message="<p>Hi {{ name }}</p>",
        slug="test-mail-html",
        is_html=True,
        is_active=True,
        enable_log=True,
    )


@pytest.fixture
def disabled_template(db, from_email):
    return MailTemplate.objects.create(
        name="Off",
        subject="Off",
        from_email=from_email,
        message="off",
        slug="test-mail-off",
        is_html=False,
        is_active=False,
    )


def _make(slug, recipient, **kwargs):
    kwargs.setdefault("backend", "mail")
    return Sender(slug, recipient, {"name": "Bob"}, **kwargs)


def test_init_unknown_slug_raises(db):
    with pytest.raises(MailTemplate.DoesNotExist):
        _make("does-not-exist", "to@example.com")


def test_send_disabled_template_returns_silently(disabled_template, mailoutbox):
    sender = _make("test-mail-off", "to@example.com")
    assert sender.send() is None
    assert mailoutbox == []


def test_get_recipient_list_string_with_email(template):
    sender = _make("test-mail", "a@b.com,c@d.com")
    assert sender._recipient_list == ["a@b.com", "c@d.com"]


def test_get_recipient_list_list_input(template):
    sender = _make("test-mail", ["a@b.com", "b@c.com"])
    assert sender._recipient_list == ["a@b.com", "b@c.com"]


def test_get_recipient_list_resolves_mail_group(template, db):
    grp = MailGroup.objects.create(name="g1", slug="grp-one")
    MailGroupEmail.objects.create(group=grp, email="member@example.com", name="m")
    sender = _make("test-mail", "grp-one")
    assert sender._recipient_list == ["member@example.com"]


def test_email_to_list_none_returns_none():
    assert Sender._email_to_list(None) is None


def test_email_to_list_strips_and_filters_empty():
    assert Sender._email_to_list(" a@b.com , ,c@d.com") == ["a@b.com", "c@d.com"]


def test_render_subject_and_message(template):
    sender = _make("test-mail", "to@example.com")
    assert sender._subject == "Hello Bob"
    assert "Hi Bob" in sender._message


def test_get_from_email_uses_template_address(template):
    sender = _make("test-mail", "to@example.com")
    assert sender._from_email == "Sender <sender@example.com>"


def test_get_from_email_kwargs_override(template):
    sender = _make("test-mail", "to@example.com", from_email="kw@example.com")
    assert sender._from_email == "kw@example.com"


def test_get_from_email_template_without_from(db):
    tpl = MailTemplate.objects.create(
        name="NoFrom",
        subject="s",
        from_email=None,
        message="m",
        slug="tpl-no-from",
        is_html=False,
    )
    assert tpl is not None
    sender = _make("tpl-no-from", "to@example.com")
    from django.conf import settings

    assert sender._from_email == settings.DEFAULT_FROM_EMAIL


def test_send_plain_message_outbox(template, mailoutbox):
    sender = _make("test-mail", "to@example.com")
    assert sender.send() == "OK"
    assert len(mailoutbox) == 1
    assert mailoutbox[0].subject == "Hello Bob"
    assert mailoutbox[0].to == ["to@example.com"]


def test_send_html_message_attaches_alternative(html_template, mailoutbox):
    sender = _make("test-mail-html", "to@example.com")
    assert sender.send() == "OK"
    assert len(mailoutbox) == 1
    msg = mailoutbox[0]
    assert any("text/html" in alt[1] for alt in msg.alternatives)


def test_send_with_cc_bcc_propagated(template, mailoutbox):
    sender = _make(
        "test-mail",
        "to@example.com",
        cc="cc@example.com",
        bcc="bcc@example.com",
    )
    sender.send()
    assert mailoutbox[0].cc == ["cc@example.com"]
    assert "bcc@example.com" in mailoutbox[0].bcc


def test_send_with_template_bcc_extends(template, mailoutbox, db):
    from dbmail.models import MailBcc

    bcc_obj = MailBcc.objects.create(email="tpl-bcc@example.com", is_active=True)
    template.bcc_email.add(bcc_obj)
    from django.core.cache import cache

    cache.clear()
    sender = _make("test-mail", "to@example.com", bcc="user-bcc@example.com")
    sender.send()
    assert "tpl-bcc@example.com" in mailoutbox[0].bcc
    assert "user-bcc@example.com" in mailoutbox[0].bcc


def test_insert_mailer_identification_header(template, settings, mailoutbox):
    settings.DB_MAILER_ADD_HEADER = True
    with mock.patch("dbmail.backends.mail.ADD_HEADER", True):
        sender = _make("test-mail", "to@example.com")
        sender.send()
    assert "X-Mailer-Wrapper" in mailoutbox[0].extra_headers


def test_no_mailer_header_when_disabled(template, mailoutbox):
    sender = _make("test-mail", "to@example.com")
    sender.send()
    assert "X-Mailer-Wrapper" not in mailoutbox[0].extra_headers


def test_update_log_creates_row_when_enabled(template, mailoutbox):
    sender = _make("test-mail", "to@example.com")
    sender.send()
    assert MailLog.objects.filter(template=template, is_sent=True).count() == 1


def test_update_log_skipped_when_template_log_disabled(db, from_email, mailoutbox):
    tpl = MailTemplate.objects.create(
        name="x",
        subject="s",
        from_email=from_email,
        message="m",
        slug="tpl-no-log",
        is_html=False,
        enable_log=False,
    )
    sender = _make("tpl-no-log", "to@example.com")
    sender.send()
    assert MailLog.objects.filter(template=tpl).count() == 0


def test_send_smtp_exception_logged_as_failure(template, mailoutbox):
    sender = _make("test-mail", "to@example.com")
    with mock.patch.object(Sender, "_send", side_effect=SMTPException("boom")):
        with pytest.raises(SMTPException):
            sender.send()
    log = MailLog.objects.get(template=template)
    assert log.is_sent is False
    assert log.error_exception.name == "SMTPException"


def test_send_ignored_exception_does_not_raise(template):
    MailLogException.objects.create(name="ValueError", ignore=True)
    from django.core.cache import cache

    cache.clear()
    sender = _make("test-mail", "to@example.com")
    with mock.patch.object(Sender, "_send", side_effect=ValueError("x")):
        assert sender.send() is None
    assert MailLog.objects.filter(template=template, is_sent=False).count() == 1


def test_send_stop_sending_exception_returns_none(template, mailoutbox):
    from dbmail.signals import pre_send

    def stop(sender, **kwargs):
        raise StopSendingException()

    pre_send.connect(stop)
    try:
        sender = _make("test-mail", "to@example.com")
        assert sender.send() is None
        assert mailoutbox == []
    finally:
        pre_send.disconnect(stop)


def test_try_to_send_retries_then_raises(template, mailoutbox):
    template.num_of_retries = 2
    template.save()
    from django.core.cache import cache

    cache.clear()
    sender = _make("test-mail", "to@example.com")
    with mock.patch("dbmail.backends.mail.time.sleep"):
        with mock.patch.object(Sender, "_send", side_effect=RuntimeError("bad")):
            with pytest.raises(RuntimeError):
                sender._try_to_send()


def test_send_with_files_attaches(template, tmp_path, mailoutbox):
    f = tmp_path / "note.txt"
    f.write_text("payload")
    sender = _make("test-mail", "to@example.com", files=[str(f)])
    sender.send()
    msg = mailoutbox[0]
    assert any(att[0] == "note.txt" for att in msg.attachments)


def test_get_connection_uses_template_credentials(db, from_email):
    cred = MailFromEmailCredential.objects.create(
        host="mail.example.com",
        port=2525,
        username="u",
        password="p",
        use_tls=True,
        fail_silently=False,
    )
    from_email.credential = cred
    from_email.save()
    tpl = MailTemplate.objects.create(
        name="cred",
        subject="s",
        from_email=from_email,
        message="m",
        slug="tpl-cred",
        is_html=False,
    )
    assert tpl is not None
    sender = _make("tpl-cred", "to@example.com")
    with mock.patch("dbmail.backends.mail.get_connection") as gc:
        gc.return_value = object()
        sender._get_connection()
        gc.assert_called_once()
        kwargs = gc.call_args.kwargs
        assert kwargs["host"] == "mail.example.com"
        assert kwargs["port"] == 2525


def test_send_via_custom_provider(template, mailoutbox):
    sender = _make("test-mail", "to@example.com", provider="dbmail.backends.fake_provider")
    fake = mock.MagicMock()
    with mock.patch("dbmail.backends.mail.import_module", return_value=fake) as imp:
        sender.send()
    imp.assert_called_with("dbmail.backends.fake_provider")
    fake.send.assert_called_once_with(sender)
    assert mailoutbox == []


def test_get_context_includes_site(template):
    sender = _make("test-mail", "to@example.com")
    assert "domain" in sender._context
    assert sender._context["name"] == "Bob"


def test_get_context_with_model_instance(template, db):
    grp = MailGroup.objects.create(name="g2", slug="g2")
    sender = Sender(
        "test-mail",
        "to@example.com",
        {"name": "X"},
        grp,
        backend="mail",
    )
    assert sender._context.get("mailgroup") is grp


def test_debug_writes_color_lines(template, capsys):
    sender = _make("test-mail", "to@example.com")
    sender.debug("Key", "value")
    out = capsys.readouterr().out
    assert "Key" in out and "value" in out


def test_debug_skips_falsy(template, capsys):
    sender = _make("test-mail", "to@example.com")
    sender.debug("Key", "")
    assert capsys.readouterr().out == ""


def test_sender_debug_send_outputs(template, capsys):
    sender = SenderDebug("test-mail", "to@example.com", {"name": "Bob"}, backend="mail")
    sender._send()
    out = capsys.readouterr().out
    assert "Provider" in out
    assert "Recipients" in out


def test_log_id_format(template):
    sender = _make("test-mail", "to@example.com")
    assert "-" in sender._log_id
