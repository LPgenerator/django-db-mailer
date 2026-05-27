"""Extended coverage for `dbmail.tasks` — branches not exercised by test_tasks.py."""

from __future__ import annotations

import sys
import types
from unittest.mock import MagicMock

import pytest

pytestmark = pytest.mark.django_db


def _install_stub_backend(mod_name: str, sender_cls):
    mod = types.ModuleType(mod_name)
    mod.Sender = sender_cls
    mod.SenderDebug = sender_cls
    sys.modules[mod_name] = mod
    return mod


def _make_sender(send_side_effect=None, capture=None):
    class Sender:
        def __init__(self, *args, **kwargs):
            if capture is not None:
                capture.update(kwargs)

        def send(self, **_):
            if send_side_effect is not None:
                raise send_side_effect
            return "sent"

    return Sender


@pytest.fixture
def stub_backend():
    name = "tests._stub_backend_for_tasks"
    yield name
    sys.modules.pop(name, None)


class TestDbSenderHappyPath:
    def test_invokes_sender_class_from_backend_module(self, stub_backend):
        from dbmail import tasks

        _install_stub_backend(stub_backend, _make_sender())
        result = tasks.db_sender.run("slug", "to@x.com", backend=stub_backend)
        assert result == "sent"

    def test_debug_path_invokes_sender_debug(self, stub_backend, monkeypatch):
        from dbmail import tasks

        monkeypatch.setattr(tasks, "DEBUG", True)
        _install_stub_backend(stub_backend, _make_sender())
        assert tasks.db_sender.run("slug", "to@x.com", backend=stub_backend) == "sent"


class TestDbSenderRetry:
    def test_retry_called_on_exception_with_countdown(self, stub_backend):
        from dbmail import tasks

        _install_stub_backend(stub_backend, _make_sender(send_side_effect=RuntimeError("boom")))
        retry_mock = MagicMock(side_effect=RuntimeError("retry-stub"))
        bound_self = MagicMock(retry=retry_mock)

        with pytest.raises(RuntimeError):
            tasks.db_sender.run.__func__(
                bound_self,
                "slug",
                "to@x.com",
                backend=stub_backend,
                retry_delay=42,
                max_retries=3,
            )

        assert retry_mock.called
        kwargs = retry_mock.call_args.kwargs
        assert kwargs["countdown"] == 42
        assert kwargs["max_retries"] == 3
        assert isinstance(kwargs["exc"], RuntimeError)

    def test_retry_disabled_reraises(self, stub_backend):
        from dbmail import tasks

        _install_stub_backend(stub_backend, _make_sender(send_side_effect=RuntimeError("boom")))
        with pytest.raises(RuntimeError, match="boom"):
            tasks.db_sender.run("slug", "to@x.com", backend=stub_backend, retry=False)

    def test_retry_no_retries_left_reraises(self, stub_backend):
        from dbmail import tasks

        _install_stub_backend(stub_backend, _make_sender(send_side_effect=RuntimeError("boom")))
        with pytest.raises(RuntimeError, match="boom"):
            tasks.db_sender.run("slug", "to@x.com", backend=stub_backend, max_retries=0)


class TestDbSenderLegacyKwargs:
    def test_time_limit_silently_stripped(self, stub_backend):
        from dbmail import tasks

        seen = {}
        _install_stub_backend(stub_backend, _make_sender(capture=seen))
        tasks.db_sender.run("slug", "to@x.com", backend=stub_backend, time_limit=99)
        assert "time_limit" not in seen

    def test_retry_delay_kwarg_stripped(self, stub_backend):
        from dbmail import tasks

        seen = {}
        _install_stub_backend(stub_backend, _make_sender(capture=seen))
        tasks.db_sender.run("slug", "to@x.com", backend=stub_backend, retry_delay=99)
        assert "retry_delay" not in seen


class TestSignalReceiverTask:
    def test_signal_receiver_task_returns_model_name(self, db, mocker):
        from dbmail import tasks
        from dbmail.models import MailFromEmail

        mocker.patch("dbmail.signals.SignalReceiver.__init__", return_value=None)
        mocker.patch("dbmail.signals.SignalReceiver.run")
        out = tasks.signal_receiver.run(MailFromEmail, instance=None)
        assert out == "mailfromemail"

    def test_signal_receiver_task_returns_none_for_no_args(self, mocker):
        from dbmail import tasks

        mocker.patch("dbmail.signals.SignalReceiver.__init__", return_value=None)
        mocker.patch("dbmail.signals.SignalReceiver.run")
        assert tasks.signal_receiver.run() is None


class TestDeferredSignalTask:
    def test_returns_ok(self, mocker):
        from dbmail import tasks

        mocker.patch("dbmail.signals.SignalReceiver.__init__", return_value=None)
        mocker.patch("dbmail.signals.SignalReceiver.run_deferred")
        out = tasks.deferred_signal.run("sender")
        assert out == "OK"


class TestMailTrackTask:
    def test_mail_track_invokes_log_track(self, mocker):
        from dbmail import tasks

        track = mocker.patch("dbmail.models.MailLogTrack.track")
        tasks.mail_track.run({"REMOTE_ADDR": "1.1.1.1"}, "encoded-payload")
        track.assert_called_once()

    def test_mail_track_retries_on_exception(self, mocker):
        from dbmail import tasks

        mocker.patch("dbmail.models.MailLogTrack.track", side_effect=ValueError("bad"))
        retry_mock = MagicMock(side_effect=ValueError("retry-stub"))
        bound_self = MagicMock(retry=retry_mock)

        with pytest.raises(ValueError):
            tasks.mail_track.run.__func__(bound_self, {}, "x")

        assert retry_mock.called
        assert isinstance(retry_mock.call_args.kwargs["exc"], ValueError)


class TestSubscriptionTask:
    def test_subscription_task_calls_notify(self, mocker):
        from dbmail import tasks

        notify = mocker.patch("dbmail.models.MailSubscription.notify")
        tasks.db_subscription.run(1, "a@b.c")
        notify.assert_called_once()
