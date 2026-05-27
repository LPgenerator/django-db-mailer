from __future__ import annotations

import logging
from typing import Any

from celery import shared_task

from dbmail.defaults import DEBUG, SEND_MAX_TIME, SEND_RETRY, SEND_RETRY_DELAY

logger = logging.getLogger(__name__)


@shared_task(
    bind=True,
    name="dbmail.db_sender",
    default_retry_delay=SEND_RETRY_DELAY,
)
def db_sender(self, *args: Any, **kwargs: Any) -> Any:
    from importlib import import_module

    retry_delay = kwargs.pop("retry_delay", SEND_RETRY_DELAY)
    # ``time_limit`` is consumed by callers via ``apply_async(time_limit=...)``;
    # passing it through kwargs is a legacy API surface that we strip silently
    # so old callers do not break.
    kwargs.pop("time_limit", SEND_MAX_TIME)
    max_retries = kwargs.pop("max_retries", SEND_RETRY)
    backend = import_module(kwargs.get("backend"))
    retry = kwargs.pop("retry", True)

    try:
        if DEBUG is True:
            return backend.SenderDebug(*args, **kwargs).send(is_celery=True)
        return backend.Sender(*args, **kwargs).send(is_celery=True)
    except Exception as exc:
        if retry and max_retries:
            logger.exception("dbmail.db_sender failed, scheduling retry")
            raise self.retry(exc=exc, countdown=retry_delay, max_retries=max_retries) from exc
        raise


@shared_task(name="dbmail.subscription")
def db_subscription(*args: Any, **kwargs: Any) -> None:
    from dbmail import import_by_string
    from dbmail.defaults import MAIL_SUBSCRIPTION_MODEL

    MailSubscription = import_by_string(MAIL_SUBSCRIPTION_MODEL)
    MailSubscription.notify(*args, **kwargs)


@shared_task(name="dbmail.signal_receiver")
def signal_receiver(*args: Any, **kwargs: Any) -> str | None:
    from dbmail.signals import SignalReceiver

    SignalReceiver(*args, **kwargs).run()
    if args:
        return args[0]._meta.model_name
    return None


@shared_task(name="dbmail.deferred_signal")
def deferred_signal(*args: Any, **kwargs: Any) -> str:
    from dbmail.signals import SignalReceiver

    SignalReceiver(*args, **kwargs).run_deferred()
    return "OK"


@shared_task(bind=True, name="dbmail.mail_track")
def mail_track(self, http_meta: dict[str, Any], encrypted: str) -> None:
    from dbmail.models import MailLogTrack

    try:
        MailLogTrack.track(http_meta, encrypted)
    except Exception as exc:
        logger.exception("dbmail.mail_track failed, scheduling retry")
        raise self.retry(exc=exc, countdown=SEND_RETRY_DELAY, max_retries=SEND_RETRY) from exc
