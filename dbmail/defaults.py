# -*- encoding: utf-8 -*-

from django.conf import settings


def get_settings(key, default):
    return getattr(settings, key, default)


PRIORITY_STEPS = get_settings('DB_MAILER_PRIORITY_STEPS', range(10))
RETRY_INTERVAL = get_settings('DB_MAILER_RETRY_INTERVAL', 3)
CELERY_QUEUE = get_settings('DB_MAILER_CELERY_QUEUE', 'default')
SHOW_CONTEXT = get_settings('DB_MAILER_SHOW_CONTEXT', False)
READ_ONLY_ENABLED = get_settings('DB_MAILER_READ_ONLY_ENABLED', True)
UPLOAD_TO = get_settings('DB_MAILER_UPLOAD_TO', 'mail_files')
