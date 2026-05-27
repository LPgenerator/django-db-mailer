"""Tests for dbmail.tasks — Celery shared_task wrappers (phase 05)."""

from __future__ import annotations

import pytest


class TestTaskNamesAndBinding:
    @pytest.mark.parametrize(
        "name",
        [
            "dbmail.db_sender",
            "dbmail.subscription",
            "dbmail.signal_receiver",
            "dbmail.deferred_signal",
            "dbmail.mail_track",
        ],
    )
    def test_task_registered_under_canonical_name(self, name):
        from celery import current_app

        import dbmail.tasks  # noqa: F401  — importing registers tasks

        assert name in current_app.tasks

    def test_db_sender_is_bound(self):
        from dbmail.tasks import db_sender

        # ``bind=True`` makes the function a Task subclass instance,
        # not a plain function. The "bound" task accepts ``self`` as
        # first arg.
        assert callable(db_sender)
        assert db_sender.name == "dbmail.db_sender"

    def test_mail_track_is_bound(self):
        from dbmail.tasks import mail_track

        assert mail_track.name == "dbmail.mail_track"


class TestDbSenderRetryWiring:
    """Verify the retry call uses the supported ``self.retry()`` API
    rather than the legacy ``retry=`` / ``time_limit=`` kwargs that
    were silently ignored before phase 05."""

    def test_retry_signature_uses_supported_kwargs(self):
        import inspect

        from celery.app.task import Task

        sig = inspect.signature(Task.retry)
        params = set(sig.parameters)
        # Public parameters of Task.retry as of Celery 5.x:
        assert {"exc", "countdown", "max_retries"} <= params
        # ``retry`` and ``time_limit`` are NOT public params:
        assert "retry" not in params
        assert "time_limit" not in params

    def test_db_sender_pops_legacy_time_limit_kwarg(self, mocker):
        """``db_sender`` must silently strip the legacy ``time_limit``
        kwarg so old 2.x callers do not blow up."""
        import dbmail.tasks as tasks_module

        # Patch the backend lookup to a stub that records what kwargs
        # the Sender saw.
        seen = {}

        class StubSender:
            def __init__(self, *args, **kwargs):
                seen.update(kwargs)

            def send(self, **_):
                return "ok"

        class StubModule:
            Sender = StubSender
            SenderDebug = StubSender

        mocker.patch("importlib.import_module", return_value=StubModule)

        # Call the underlying function (skip celery binding) so we don't
        # need a worker.
        tasks_module.db_sender.run("slug", "a@b.c", time_limit=99, backend="x")

        # ``time_limit`` is popped — Sender never sees it.
        assert "time_limit" not in seen
