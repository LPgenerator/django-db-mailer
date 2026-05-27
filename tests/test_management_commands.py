"""Tests for `dbmail.management.commands.*` — coverage for CLI entrypoints."""

from __future__ import annotations

import datetime
from unittest.mock import patch

import pytest
from django.core.management import call_command

pytestmark = pytest.mark.django_db


@pytest.fixture
def template(db):
    from dbmail.models import MailFromEmail, MailTemplate

    sender = MailFromEmail.objects.create(name="from", email="from@example.com")
    return MailTemplate.objects.create(
        name="t",
        subject="s",
        slug="t-slug",
        message="hi {{ user_email }}",
        from_email=sender,
        is_active=True,
    )


class TestCleanDbmailCache:
    def test_command_calls_clean_cache_on_template_and_apikey(self, template):
        from dbmail.models import ApiKey, MailTemplate

        with patch.object(MailTemplate, "clean_cache") as mt_clean, patch.object(ApiKey, "clean_cache") as api_clean:
            call_command("clean_dbmail_cache")

        assert mt_clean.called
        assert api_clean.called


class TestUpdateDbmailCache:
    def test_command_walks_all_templates(self, template):
        from dbmail.models import MailTemplate

        with patch.object(MailTemplate, "get_template") as get_t:
            call_command("update_dbmail_cache")

        get_t.assert_called_with(template.slug)


class TestCleanDbmailLogs:
    def test_command_deletes_old_logs(self, template, settings):
        from dbmail.models import MailLog

        old = MailLog.objects.create(template=template, is_sent=True)
        # Force `created` into the past — auto_now_add prevents direct set.
        past = datetime.datetime.now(tz=datetime.timezone.utc) - datetime.timedelta(days=400)
        MailLog.objects.filter(pk=old.pk).update(created=past)

        recent = MailLog.objects.create(template=template, is_sent=True)

        # Default LOGS_EXPIRE_DAYS=7.
        call_command("clean_dbmail_logs")

        assert not MailLog.objects.filter(pk=old.pk).exists()
        assert MailLog.objects.filter(pk=recent.pk).exists()

    def test_command_keeps_logs_within_window(self, template):
        from dbmail.models import MailLog

        log = MailLog.objects.create(template=template, is_sent=True)
        call_command("clean_dbmail_logs")
        assert MailLog.objects.filter(pk=log.pk).exists()


class TestDbmailTestSend:
    def test_send_test_msg_invokes_db_sender(self, template):
        from dbmail.management.commands.dbmail_test_send import send_test_msg

        with patch("dbmail.management.commands.dbmail_test_send.db_sender") as ds:
            send_test_msg(template.pk, "to@example.com", use_celery=False)

        assert ds.called
        # When ``user`` is None, db_sender is called as
        # ``db_sender(slug, email, context, **kwargs)`` without a user kwarg.
        args, kwargs = ds.call_args
        assert args[0] == template.slug
        assert args[1] == "to@example.com"
        assert "user_email" in args[2]

    def test_handle_dispatches_with_default_args(self, template):
        with patch("dbmail.management.commands.dbmail_test_send.send_test_msg") as send, patch("builtins.print") as p:
            call_command("dbmail_test_send", "--pk", str(template.pk), "--email", "x@y.z")
        assert send.called
        assert p.called

    def test_get_kwargs_with_provider_and_backend(self):
        from dbmail.management.commands.dbmail_test_send import Command

        opts = {"celery": False, "provider": "twilio", "backend": "sms"}
        kwargs = Command.get_kwargs(opts)
        assert kwargs["use_celery"] is True
        assert kwargs["provider"] == "twilio"
        assert "backend" in kwargs


class TestSendDbmailDeferredSignal:
    def test_handle_processes_due_dispatches(self, template):
        from dbmail.models import SignalDeferredDispatch

        # Make a JSON-only payload — interval=0 ⇒ eta == now.
        SignalDeferredDispatch.add_task(args=[1], kwargs={}, params={}, interval=0)
        SignalDeferredDispatch.add_task(args=[2], kwargs={}, params={}, interval=0)
        # Future eta — should NOT be picked up.
        SignalDeferredDispatch.add_task(args=[3], kwargs={}, params={}, interval=3600)

        with patch.object(SignalDeferredDispatch, "run_task") as run_t:
            call_command("send_dbmail_deferred_signal")

        # Two due tasks ran.
        assert run_t.call_count == 2

    def test_purge_true_deletes_after_run(self, settings):
        from dbmail.models import SignalDeferredDispatch

        SignalDeferredDispatch.add_task(args=[1], kwargs={}, params={}, interval=0)
        # SIGNAL_DB_DEFERRED_PURGE defaults to True — call_command will delete.
        with patch.object(SignalDeferredDispatch, "run_task"):
            call_command("send_dbmail_deferred_signal")

        assert SignalDeferredDispatch.objects.count() == 0

    def test_purge_false_marks_done(self, settings, monkeypatch):
        from dbmail.management.commands import send_dbmail_deferred_signal as cmd
        from dbmail.models import SignalDeferredDispatch

        monkeypatch.setattr(cmd, "SIGNAL_DB_DEFERRED_PURGE", False)
        row = SignalDeferredDispatch.add_task(args=[1], kwargs={}, params={}, interval=0)
        with patch.object(SignalDeferredDispatch, "run_task"):
            call_command("send_dbmail_deferred_signal")
        row.refresh_from_db()
        assert row.done is True


class TestLoadDbmailBaseTemplates:
    def test_command_calls_loaddata(self):
        with patch("dbmail.management.commands.load_dbmail_base_templates.call_command") as cc:
            call_command("load_dbmail_base_templates")
        cc.assert_called_once_with("loaddata", "mailgun_base_templates", app_label="dbmail")
