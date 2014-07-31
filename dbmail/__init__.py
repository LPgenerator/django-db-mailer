from sys import argv
from datetime import datetime
from django.conf import settings
from signals import initial_signals

VERSION = (2, 0)


def get_version():
    return '.'.join(map(str, VERSION))


def celery_supported():
    try:
        import tasks

        if 'djcelery' not in settings.INSTALLED_APPS:
            raise ImportError
        return True
    except ImportError:
        return False


def send_db_mail(slug, recipient, *args, **kwargs):
    from dbmail.defaults import CELERY_QUEUE, SEND_MAX_TIME
    from dbmail.models import MailTemplate
    from dbmail.send_mail import SendMail

    args = (slug, recipient) + args
    send_after = kwargs.pop('send_after', None)
    send_at_date = kwargs.pop('send_at_date', None)

    if celery_supported():
        import tasks

        if 'djcelery' not in settings.INSTALLED_APPS:
            raise ImportError

        template = MailTemplate.get_template(slug=slug)

        max_retries = kwargs.get('max_retries', None)
        if max_retries is None and template.num_of_retries:
            kwargs['max_retries'] = template.num_of_retries

        options = {
            'args': args, 'kwargs': kwargs,
            'queue': kwargs.pop('queue', CELERY_QUEUE),
            'time_limit': kwargs.get('time_limit', SEND_MAX_TIME),
            'priority': template.priority,
        }

        if send_at_date is not None and isinstance(send_at_date, datetime):
            options.update({'eta': send_at_date})
        if send_after is not None:
            options.update({'countdown': send_after})

        tasks.send_db_mail.apply_async(**options)
    else:
        SendMail(*args, **kwargs).send()


for cmd in ['schemamigration', 'migrate']:
    if cmd in argv:
        break
else:
    initial_signals()
