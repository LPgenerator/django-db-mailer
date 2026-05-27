from __future__ import annotations

import sys
from datetime import datetime
from typing import Any

__version__: str = "3.0.0rc2"

# Back-compat tuple for code that imports `from dbmail import VERSION`.
# `__version__` (str) is the canonical source; this tuple tracks the numeric
# release components only (no dev/rc suffixes).
VERSION: tuple[int, int, int] = (3, 0, 0)


__all__ = [
    "VERSION",
    "__version__",
    "app_installed",
    "celery_supported",
    "db_sender",
    "get_model",
    "get_version",
    "import_by_string",
    "initial_signals",
    "send_db_bot",
    "send_db_mail",
    "send_db_push",
    "send_db_sms",
    "send_db_subscription",
    "send_db_tts",
]


def get_version() -> str:
    return __version__


def app_installed(app: str) -> bool:
    from django.conf import settings

    return app in settings.INSTALLED_APPS


def celery_supported() -> bool:
    try:
        import celery
    except ImportError:
        return False
    return True


def db_sender(slug: str, recipient: Any, *args: Any, **kwargs: Any) -> Any:
    from importlib import import_module

    from dbmail.defaults import (
        BACKEND,
        CELERY_QUEUE,
        DEBUG,
        ENABLE_CELERY,
        SEND_MAX_TIME,
    )
    from dbmail.models import MailTemplate

    args = (slug, recipient) + args
    send_after = kwargs.pop("send_after", None)
    send_at_date = kwargs.pop("send_at_date", None)
    _use_celery = kwargs.pop("use_celery", ENABLE_CELERY)
    use_celery = ENABLE_CELERY and _use_celery
    backend = kwargs.get("backend", BACKEND["mail"])

    if celery_supported() and use_celery is True:
        import dbmail.tasks

        template = MailTemplate.get_template(slug=slug)
        max_retries = kwargs.get("max_retries", None)
        send_after = send_after if send_after else template.interval
        if max_retries is None and template.num_of_retries:
            kwargs["max_retries"] = template.num_of_retries

        options = {
            "args": args,
            "kwargs": kwargs,
            "queue": kwargs.pop("queue", CELERY_QUEUE),
            "time_limit": kwargs.get("time_limit", SEND_MAX_TIME),
            "priority": template.priority,
        }

        if send_at_date is not None and isinstance(send_at_date, datetime):
            options.update({"eta": send_at_date})
        if send_after is not None:
            options.update({"countdown": send_after})
        if template.is_active:
            return dbmail.tasks.db_sender.apply_async(**options)
        return None

    module = import_module(backend)
    if DEBUG is True:
        return module.SenderDebug(*args, **kwargs).send(is_celery=False)
    return module.Sender(*args, **kwargs).send(is_celery=False)


def send_db_mail(*args: Any, **kwargs: Any) -> Any:
    """Send a templated email through the dbmail pipeline.

    Positional args: ``slug, recipient, *context``. Keyword args are
    forwarded to the backend ``Sender``.

    :keyword correlation_id: Optional business correlation key (e.g.
        ``order_id``, ``request_id``) persisted on the resulting
        :class:`~dbmail.models.MailLog` row for distributed tracing.
        Maximum length 64 characters; longer values are rejected by
        Django's CharField validation. See ADR-0011.
    """
    from dbmail.defaults import BACKEND

    kwargs["backend"] = kwargs.pop("backend", BACKEND["mail"])
    return db_sender(*args, **kwargs)


def send_db_sms(*args: Any, **kwargs: Any) -> Any:
    from dbmail.defaults import BACKEND, SMS_QUEUE

    kwargs["backend"] = kwargs.pop("backend", BACKEND["sms"])
    kwargs["queue"] = kwargs.pop("queue", SMS_QUEUE)
    return db_sender(*args, **kwargs)


def send_db_tts(*args: Any, **kwargs: Any) -> Any:
    from dbmail.defaults import BACKEND, TTS_QUEUE

    kwargs["backend"] = kwargs.pop("backend", BACKEND["tts"])
    kwargs["queue"] = kwargs.pop("queue", TTS_QUEUE)
    return db_sender(*args, **kwargs)


def send_db_push(*args: Any, **kwargs: Any) -> Any:
    from dbmail.defaults import BACKEND, PUSH_QUEUE

    kwargs["backend"] = kwargs.pop("backend", BACKEND["push"])
    kwargs["queue"] = kwargs.pop("queue", PUSH_QUEUE)
    return db_sender(*args, **kwargs)


def send_db_bot(*args: Any, **kwargs: Any) -> Any:
    from dbmail.defaults import BACKEND, BOT_QUEUE

    kwargs["backend"] = kwargs.pop("backend", BACKEND["bot"])
    kwargs["queue"] = kwargs.pop("queue", BOT_QUEUE)
    return db_sender(*args, **kwargs)


def send_db_subscription(*args: Any, **kwargs: Any) -> Any:
    from dbmail.defaults import (
        ENABLE_CELERY,
        MAIL_SUBSCRIPTION_MODEL,
        SEND_MAX_TIME,
        SUBSCRIPTION_QUEUE,
    )

    MailSubscription = import_by_string(MAIL_SUBSCRIPTION_MODEL)

    use_celery = ENABLE_CELERY and kwargs.pop("use_celery", ENABLE_CELERY)
    options = {
        "time_limit": kwargs.pop("time_limit", SEND_MAX_TIME),
        "queue": kwargs.pop("queue", SUBSCRIPTION_QUEUE),
        "args": args,
        "kwargs": kwargs,
    }

    if celery_supported() and use_celery is True:
        from dbmail.tasks import db_subscription

        return db_subscription.apply_async(**options)
    kwargs["use_celery"] = use_celery
    return MailSubscription.notify(*args, **kwargs)


def initial_signals() -> None:
    from django.db.utils import DatabaseError, IntegrityError

    skip_commands = {
        "schemamigration",
        "migrate",
        "test",
        "createsuperuser",
        "makemigrations",
        "collectstatic",
        "compilemessages",
    }
    if any(cmd in sys.argv for cmd in skip_commands):
        return
    try:
        from dbmail.signals import initial_signals as init_signals

        init_signals()
    except (ImportError, DatabaseError, IntegrityError):
        pass


def import_by_string(dotted_path: str) -> Any:
    """Import a class or callable by its dotted path."""
    from django.utils.module_loading import import_string

    return import_string(dotted_path)


def get_model(*args: Any, **kwargs: Any) -> Any:
    from django.apps import apps

    return apps.get_model(*args, **kwargs)
