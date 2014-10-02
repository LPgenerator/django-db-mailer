# -*- coding: utf-8 -*-

from celery import task
from dbmail.defaults import SEND_RETRY_DELAY, SEND_RETRY, SEND_MAX_TIME


@task(name='dbmail.send_db_mail', default_retry_delay=SEND_RETRY_DELAY)
def send_db_mail(*args, **kwargs):
    from dbmail.send_mail import SendMail

    retry_delay = kwargs.pop('retry_delay', SEND_RETRY_DELAY)
    time_limit = kwargs.pop('time_limit', SEND_MAX_TIME)
    max_retries = kwargs.pop('max_retries', SEND_RETRY)
    retry = kwargs.pop('retry', True)

    try:
        return SendMail(*args, **kwargs).send(is_celery=True)
    except Exception, exc:
        if retry is True and max_retries:
            raise send_db_mail.retry(
                retry=retry, max_retries=max_retries,
                countdown=retry_delay, exc=exc,
                time_limit=time_limit,
            )
        raise


@task(name='dbmail.signal_receiver')
def signal_receiver(*args, **kwargs):
    from dbmail.signals import SignalReceiver

    return SignalReceiver(*args, **kwargs)
