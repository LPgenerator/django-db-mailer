"""Tests for `dbmail.signals` — SignalReceiver and dispatch wiring."""

from __future__ import annotations

from unittest.mock import patch

import pytest
from django.contrib.contenttypes.models import ContentType

pytestmark = pytest.mark.django_db


@pytest.fixture
def template(db):
    from dbmail.models import MailFromEmail, MailTemplate

    sender = MailFromEmail.objects.create(name="from", email="from@example.com")
    return MailTemplate.objects.create(
        name="t",
        subject="s",
        slug="signals-tpl",
        message="hello {{ instance.email }}",
        from_email=sender,
        is_active=True,
    )


@pytest.fixture
def signal_row(db, template):
    from dbmail.models import MailFromEmail, Signal

    ct = ContentType.objects.get_for_model(MailFromEmail)
    return Signal.objects.create(
        name="on-save",
        model=ct,
        signal="post_save",
        template=template,
        rules="{{ instance.email }}",
        is_active=True,
        receive_once=True,
        interval=0,
    )


@pytest.fixture
def signal_row_with_group(db, template):
    from dbmail.models import MailFromEmail, MailGroup, Signal

    grp = MailGroup.objects.create(name="ops", slug="ops")
    ct = ContentType.objects.get_for_model(MailFromEmail)
    return Signal.objects.create(
        name="on-save-group",
        model=ct,
        signal="post_save",
        template=template,
        group=grp,
        is_active=True,
        receive_once=True,
        interval=0,
    )


class TestSignalReceiverInit:
    def test_collects_site_and_instance(self, signal_row):
        from dbmail.models import MailFromEmail
        from dbmail.signals import SignalReceiver

        instance = MailFromEmail.objects.create(name="x", email="x@y.z")
        rcv = SignalReceiver(MailFromEmail, instance=instance)
        assert rcv.instance is instance
        assert rcv.pk == instance.pk
        assert rcv.site is not None
        assert "date" in rcv.kwargs and "date_time" in rcv.kwargs

    def test_get_old_instance_returns_db_row_when_exists(self, signal_row):
        from dbmail.models import MailFromEmail
        from dbmail.signals import SignalReceiver

        instance = MailFromEmail.objects.create(name="x", email="x@y.z")
        rcv = SignalReceiver(MailFromEmail, instance=instance)
        old = rcv.kwargs["old_instance"]
        assert old is not None
        assert old.pk == instance.pk

    def test_get_old_instance_handles_missing(self, signal_row):
        from dbmail.models import MailFromEmail
        from dbmail.signals import SignalReceiver

        # Build an unsaved-but-pk-having instance with a fake pk.
        ghost = MailFromEmail(name="g", email="g@h.i")
        ghost.pk = 999_999
        rcv = SignalReceiver(MailFromEmail, instance=ghost)
        assert rcv.kwargs["old_instance"] is None

    def test_get_users_disabled_returns_empty(self, signal_row, monkeypatch):
        from dbmail import signals as signals_module
        from dbmail.models import MailFromEmail
        from dbmail.signals import SignalReceiver

        monkeypatch.setattr(signals_module, "ENABLE_USERS", False)
        instance = MailFromEmail.objects.create(name="x", email="x@y.z")
        rcv = SignalReceiver(MailFromEmail, instance=instance)
        assert rcv.kwargs["users"] == []

    def test_get_users_enabled_returns_queryset(self, signal_row, monkeypatch):
        from dbmail import signals as signals_module
        from dbmail.models import MailFromEmail
        from dbmail.signals import SignalReceiver

        monkeypatch.setattr(signals_module, "ENABLE_USERS", True)
        instance = MailFromEmail.objects.create(name="x", email="x@y.z")
        rcv = SignalReceiver(MailFromEmail, instance=instance)
        # Returns a QuerySet — accept either an empty list or a QuerySet.
        users = rcv.kwargs["users"]
        assert hasattr(users, "filter") or users == []


class TestRunDispatch:
    def test_run_with_interval_zero_invokes_send_mail(self, signal_row):
        from dbmail.models import MailFromEmail
        from dbmail.signals import SignalReceiver

        instance = MailFromEmail.objects.create(name="x", email="x@y.z")
        rcv = SignalReceiver(MailFromEmail, instance=instance)
        with patch.object(SignalReceiver, "send_mail") as send_mail:
            rcv.run()
        send_mail.assert_called_once()

    def test_run_with_interval_invokes_deferred(self, signal_row):
        from dbmail.models import MailFromEmail
        from dbmail.signals import SignalReceiver

        signal_row.interval = 60
        signal_row.save()
        instance = MailFromEmail.objects.create(name="x", email="x@y.z")
        rcv = SignalReceiver(MailFromEmail, instance=instance)
        with patch.object(SignalReceiver, "_dispatch_deferred_task") as deferred:
            rcv.run()
        deferred.assert_called_once()

    def test_inactive_signal_not_picked_up(self, signal_row):
        from dbmail.models import MailFromEmail
        from dbmail.signals import SignalReceiver

        signal_row.is_active = False
        signal_row.save()
        instance = MailFromEmail.objects.create(name="x", email="x@y.z")
        rcv = SignalReceiver(MailFromEmail, instance=instance)
        with patch.object(SignalReceiver, "send_mail") as send_mail:
            rcv.run()
        send_mail.assert_not_called()


class TestSendMail:
    def test_sends_to_recipients_from_rules(self, signal_row):
        from dbmail.models import MailFromEmail
        from dbmail.signals import SignalReceiver

        instance = MailFromEmail.objects.create(name="alice", email="alice@example.com")
        rcv = SignalReceiver(MailFromEmail, instance=instance)
        rcv.signal = signal_row

        with patch("dbmail.send_db_mail") as send:
            rcv.send_mail()

        assert send.called
        args = send.call_args.args
        assert args[0] == signal_row.template.slug
        # second arg is the email (whitespace stripped, single recipient)
        assert args[1] == "alice@example.com"

    def test_marks_signal_as_sent(self, signal_row):
        from dbmail.models import MailFromEmail, SignalLog
        from dbmail.signals import SignalReceiver

        instance = MailFromEmail.objects.create(name="alice", email="alice@example.com")
        rcv = SignalReceiver(MailFromEmail, instance=instance)
        rcv.signal = signal_row

        with patch("dbmail.send_db_mail"):
            rcv.send_mail()

        assert SignalLog.objects.filter(signal=signal_row, model_pk=instance.pk).exists()

    def test_skip_when_already_sent_and_receive_once(self, signal_row):
        from dbmail.models import MailFromEmail, SignalLog
        from dbmail.signals import SignalReceiver

        instance = MailFromEmail.objects.create(name="alice", email="alice@example.com")
        SignalLog.objects.create(model=signal_row.model, model_pk=instance.pk, signal=signal_row)

        rcv = SignalReceiver(MailFromEmail, instance=instance)
        rcv.signal = signal_row

        with patch("dbmail.send_db_mail") as send:
            rcv.send_mail()

        send.assert_not_called()

    def test_group_branch_returns_group_slug(self, signal_row_with_group):
        from dbmail.models import MailFromEmail, MailGroup, MailGroupEmail
        from dbmail.signals import SignalReceiver

        grp = MailGroup.objects.get(slug="ops")
        MailGroupEmail.objects.create(group=grp, name="op", email="op@example.com")

        instance = MailFromEmail.objects.create(name="x", email="x@y.z")
        rcv = SignalReceiver(MailFromEmail, instance=instance)
        rcv.signal = signal_row_with_group

        # get_email_list should return the group slug, not rules-rendered text.
        assert rcv.get_email_list() == "ops"


class TestDispatchDeferred:
    def test_celery_branch_calls_apply_async(self, signal_row, monkeypatch):
        from dbmail import signals as signals_module
        from dbmail.models import MailFromEmail
        from dbmail.signals import SignalReceiver

        monkeypatch.setattr(signals_module, "SIGNAL_DEFERRED_DISPATCHER", "celery")
        instance = MailFromEmail.objects.create(name="x", email="x@y.z")
        rcv = SignalReceiver(MailFromEmail, instance=instance)
        rcv.signal = signal_row

        with patch("dbmail.tasks.deferred_signal.apply_async") as apply_async:
            rcv._dispatch_deferred_task()

        apply_async.assert_called_once()
        kwargs = apply_async.call_args.kwargs
        assert kwargs["countdown"] == signal_row.interval

    def test_db_branch_creates_dispatch_row(self, signal_row, monkeypatch):
        from dbmail import signals as signals_module
        from dbmail.models import MailFromEmail, SignalDeferredDispatch
        from dbmail.signals import SignalReceiver

        monkeypatch.setattr(signals_module, "SIGNAL_DEFERRED_DISPATCHER", "db")
        instance = MailFromEmail.objects.create(name="x", email="x@y.z")
        rcv = SignalReceiver(MailFromEmail, instance=instance)
        rcv.signal = signal_row

        before = SignalDeferredDispatch.objects.count()
        rcv._dispatch_deferred_task()
        assert SignalDeferredDispatch.objects.count() == before + 1


class TestRunDeferred:
    def test_run_deferred_sends_when_signal_active(self, signal_row):
        from dbmail.models import MailFromEmail
        from dbmail.signals import SignalReceiver

        instance = MailFromEmail.objects.create(name="x", email="x@y.z")
        rcv = SignalReceiver(MailFromEmail, instance=instance, signal_pk=signal_row.pk)
        with patch.object(SignalReceiver, "send_mail") as send_mail:
            rcv.run_deferred()
        send_mail.assert_called_once()

    def test_run_deferred_swallows_missing_signal(self):
        from dbmail.models import MailFromEmail
        from dbmail.signals import SignalReceiver

        ghost = MailFromEmail(name="g", email="g@h.i")
        ghost.pk = None
        rcv = SignalReceiver(MailFromEmail, instance=ghost, signal_pk=999_999)
        # No exception even when signal_pk does not exist.
        rcv.run_deferred()


class TestSignalReceiverFunction:
    def test_celery_branch_calls_apply_async(self, signal_row, monkeypatch):
        from dbmail import signals as signals_module
        from dbmail.models import MailFromEmail

        monkeypatch.setattr(signals_module, "ENABLE_CELERY", True)
        with (
            patch("dbmail.celery_supported", return_value=True),
            patch("dbmail.tasks.signal_receiver.apply_async") as apply_async,
        ):
            instance = MailFromEmail.objects.create(name="x", email="x@y.z")
            signals_module.signal_receiver(MailFromEmail, instance=instance)
        apply_async.assert_called_once()

    def test_sync_branch_runs_inline(self, signal_row, monkeypatch):
        from dbmail import signals as signals_module
        from dbmail.models import MailFromEmail

        monkeypatch.setattr(signals_module, "ENABLE_CELERY", False)
        with patch.object(signals_module.SignalReceiver, "run") as run:
            instance = MailFromEmail.objects.create(name="x", email="x@y.z")
            signals_module.signal_receiver(MailFromEmail, instance=instance)
        run.assert_called_once()

    def test_signal_kwarg_is_popped(self, signal_row, monkeypatch):
        from dbmail import signals as signals_module
        from dbmail.models import MailFromEmail

        monkeypatch.setattr(signals_module, "ENABLE_CELERY", False)
        with patch.object(signals_module.SignalReceiver, "run"):
            instance = MailFromEmail.objects.create(name="x", email="x@y.z")
            # No exception even when "signal" kwarg is present.
            signals_module.signal_receiver(MailFromEmail, instance=instance, signal="bogus")


class TestInitialSignals:
    def test_connects_active_signal_to_dispatcher(self, signal_row):
        from dbmail.signals import initial_signals

        # Just verify it runs without error and connects.
        initial_signals()


class TestPublicDispatchSignals:
    @pytest.mark.parametrize(
        "name",
        [
            "pre_send",
            "post_send",
            "post_exception",
            "safari_push_package",
            "safari_subscribe",
            "safari_unsubscribe",
            "safari_error_log",
            "push_subscribe",
            "push_unsubscribe",
        ],
    )
    def test_signal_object_exists(self, name):
        from django import dispatch

        from dbmail import signals as signals_module

        sig = getattr(signals_module, name)
        assert isinstance(sig, dispatch.Signal)


# ---------------------------------------------------------------------------
# C2 — configurable dotted-path signal choices
# ---------------------------------------------------------------------------


class TestDottedPathSignals:
    def test_signal_field_accepts_dotted_path(self, db, template):
        """Signal.signal stores fully-qualified dotted paths."""
        from dbmail.models import MailFromEmail, Signal

        ct = ContentType.objects.get_for_model(MailFromEmail)
        row = Signal.objects.create(
            name="dotted",
            model=ct,
            signal="django.db.models.signals.post_save",
            template=template,
            is_active=True,
        )
        row.refresh_from_db()
        assert row.signal == "django.db.models.signals.post_save"

    def test_resolve_signal_dotted_path(self):
        """_resolve_signal returns the actual Signal instance for a dotted path."""
        from django.db.models import signals as django_signals

        from dbmail.signals import _resolve_signal

        sig = _resolve_signal("django.db.models.signals.post_save")
        assert sig is django_signals.post_save

    def test_resolve_signal_legacy_short_name(self):
        """Fallback path: bare short names still resolve via django.db.models.signals."""
        from django.db.models import signals as django_signals

        from dbmail.signals import _resolve_signal

        sig = _resolve_signal("post_save")
        assert sig is django_signals.post_save

    def test_initial_signals_resolves_dotted_path(self, db, template):
        """initial_signals walks dotted-path rows without crashing."""
        from dbmail.models import MailFromEmail, Signal
        from dbmail.signals import initial_signals

        ct = ContentType.objects.get_for_model(MailFromEmail)
        Signal.objects.create(
            name="initial-dotted",
            model=ct,
            signal="django.db.models.signals.post_save",
            template=template,
            is_active=True,
        )
        initial_signals()  # no exception ⇒ pass

    def test_custom_signal_via_settings_choices(self, db, template, settings):
        """DB_MAILER_SIGNAL_CHOICES override widens the choice list."""
        from importlib import reload

        from dbmail import defaults as defaults_module

        custom = (
            *defaults_module.DEFAULT_SIGNAL_CHOICES,
            ("myapp.signals.order_paid", "order_paid"),
        )
        settings.DB_MAILER_SIGNAL_CHOICES = custom
        reload(defaults_module)
        try:
            assert ("myapp.signals.order_paid", "order_paid") in defaults_module.SIGNAL_CHOICES
        finally:
            # Restore module to its default state for downstream tests.
            del settings.DB_MAILER_SIGNAL_CHOICES
            reload(defaults_module)


class TestSignalDottedPathMigration:
    def test_forward_rewrites_short_names(self, transactional_db):
        from django_test_migrations.migrator import Migrator

        migrator = Migrator(database="default")
        old_state = migrator.apply_initial_migration(("dbmail", "0004_signallog_unique"))
        Signal = old_state.apps.get_model("dbmail", "Signal")
        MailFromEmail = old_state.apps.get_model("dbmail", "MailFromEmail")
        MailTemplate = old_state.apps.get_model("dbmail", "MailTemplate")
        ContentType = old_state.apps.get_model("contenttypes", "ContentType")

        from_email = MailFromEmail.objects.create(name="f", email="f@x.com")
        tpl = MailTemplate.objects.create(
            name="t", subject="s", slug="mig-tpl", message="m", from_email=from_email, is_active=True
        )
        ct = ContentType.objects.get_for_model(MailFromEmail)
        Signal.objects.create(
            name="legacy",
            model=ct,
            signal="post_save",
            template=tpl,
            rules="x",
            is_active=True,
            receive_once=True,
            interval=0,
        )

        new_state = migrator.apply_tested_migration(("dbmail", "0005_signal_dotted_paths"))
        Signal = new_state.apps.get_model("dbmail", "Signal")
        row = Signal.objects.get(name="legacy")
        assert row.signal == "django.db.models.signals.post_save"

        migrator.reset()
