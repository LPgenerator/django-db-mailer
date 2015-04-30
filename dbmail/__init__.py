from datetime import datetime
import sys


VERSION = (2, 1, 0)

default_app_config = 'dbmail.apps.DBMailConfig'


def get_version():
    return '.'.join(map(str, VERSION))


def app_installed(app):
    from django.conf import settings

    return app in settings.INSTALLED_APPS


def celery_supported():
    try:
        import tasks

        if not app_installed('djcelery'):
            raise ImportError
        return True
    except ImportError:
        return False


def db_sender(slug, recipient, *args, **kwargs):
    from django.utils.importlib import import_module
    from dbmail.defaults import (
        CELERY_QUEUE, SEND_MAX_TIME, ENABLE_CELERY, BACKEND)
    from dbmail.models import MailTemplate

    args = (slug, recipient) + args
    send_after = kwargs.pop('send_after', None)
    send_at_date = kwargs.pop('send_at_date', None)
    _use_celery = kwargs.pop('use_celery', ENABLE_CELERY)
    use_celery = ENABLE_CELERY and _use_celery
    backend = kwargs.get('backend', BACKEND['mail'])

    if celery_supported() and use_celery is True:
        import tasks

        template = MailTemplate.get_template(slug=slug)
        max_retries = kwargs.get('max_retries', None)
        send_after = send_after if send_after else template.interval
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
        if template.is_active:
            return tasks.db_sender.apply_async(**options)
    else:
        module = import_module(backend)
        return module.Sender(*args, **kwargs).send(is_celery=False)


def send_db_mail(*args, **kwargs):
    from dbmail.defaults import BACKEND

    kwargs['backend'] = kwargs.pop('backend', BACKEND['mail'])
    return db_sender(*args, **kwargs)


def send_db_sms(*args, **kwargs):
    from dbmail.defaults import BACKEND

    kwargs['backend'] = kwargs.pop('backend', BACKEND['sms'])
    return db_sender(*args, **kwargs)


def send_db_tts(*args, **kwargs):
    from dbmail.defaults import BACKEND

    kwargs['backend'] = kwargs.pop('backend', BACKEND['tts'])
    return db_sender(*args, **kwargs)


def send_db_push(*args, **kwargs):
    from dbmail.defaults import BACKEND

    kwargs['backend'] = kwargs.pop('backend', BACKEND['push'])
    return db_sender(*args, **kwargs)


def initial_signals():
    from django.db.utils import DatabaseError, IntegrityError

    for cmd in ['schemamigration', 'migrate', 'syncdb',
                'test', 'createsuperuser', 'makemigrations']:
        if cmd in sys.argv:
            break
    else:
        try:
            from dbmail.signals import initial_signals

            initial_signals()
        except (ImportError, DatabaseError, IntegrityError):
            pass
