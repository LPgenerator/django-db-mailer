# -*- coding: utf-8 -*-

from django.core import signing
from celery import task

from dbmail.defaults import SEND_RETRY_DELAY, SEND_RETRY, SEND_MAX_TIME, DEBUG
from dbmail.utils import get_ip


@task(name='dbmail.db_sender', default_retry_delay=SEND_RETRY_DELAY)
def db_sender(*args, **kwargs):
    from dbmail import import_module

    retry_delay = kwargs.pop('retry_delay', SEND_RETRY_DELAY)
    time_limit = kwargs.pop('time_limit', SEND_MAX_TIME)
    max_retries = kwargs.pop('max_retries', SEND_RETRY)
    backend = import_module(kwargs.get('backend'))
    retry = kwargs.pop('retry', True)

    try:
        if DEBUG is True:
            return backend.SenderDebug(*args, **kwargs).send(is_celery=True)
        return backend.Sender(*args, **kwargs).send(is_celery=True)
    except Exception as exc:
        if retry is True and max_retries:
            raise db_sender.retry(
                retry=retry, max_retries=max_retries,
                countdown=retry_delay, exc=exc,
                time_limit=time_limit,
            )
        raise


@task(name='dbmail.subscription')
def db_subscription(*args, **kwargs):
    from dbmail import import_by_string
    from dbmail.defaults import MAIL_SUBSCRIPTION_MODEL

    MailSubscription = import_by_string(MAIL_SUBSCRIPTION_MODEL)

    MailSubscription.notify(*args, **kwargs)


@task(name='dbmail.signal_receiver')
def signal_receiver(*args, **kwargs):
    from dbmail.signals import SignalReceiver

    SignalReceiver(*args, **kwargs).run()
    if len(args):
        return args[0]._meta.module_name


@task(name='dbmail.deferred_signal')
def deferred_signal(*args, **kwargs):
    from dbmail.signals import SignalReceiver

    SignalReceiver(*args, **kwargs).run_deferred()
    return 'OK'


@task(name='dbmail.mail_track')
def mail_track(http_meta, encrypted):
    from dbmail.models import MailLogTrack, MailLog

    class Request(object):
        META = http_meta

    try:
        request = Request()

        mail_log_id = signing.loads(encrypted)
        mail_log = MailLog.objects.get(log_id=mail_log_id)

        track_log = MailLogTrack.objects.filter(mail_log=mail_log)
        if not track_log.exists():
            MailLogTrack.objects.create(
                mail_log=mail_log,
                ip=get_ip(request),
                ua=request.META.get('HTTP_USER_AGENT'),
                is_read=True,
            )
        else:
            track_log[0].save()
    except (signing.BadSignature, MailLog.DoesNotExist):
        pass
    except Exception as exc:
        raise mail_track.retry(
            retry=True, max_retries=SEND_RETRY,
            countdown=SEND_RETRY_DELAY, exc=exc,
        )
