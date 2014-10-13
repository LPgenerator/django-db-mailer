# -*- encoding: utf-8 -*-

from django.utils.translation import ugettext_lazy as _
from django.conf import settings


def get_settings(key, default):
    return getattr(settings, key, default)


PRIORITY_STEPS = get_settings('DB_MAILER_PRIORITY_STEPS', (
    (0, _("High")),
    (3, _("Medium")),
    (6, _("Low")),
    (9, _("Deferred")),
))
CELERY_QUEUE = get_settings('DB_MAILER_CELERY_QUEUE', 'default')
ENABLE_CELERY = get_settings('DB_MAILER_ENABLE_CELERY', True)
SHOW_CONTEXT = get_settings('DB_MAILER_SHOW_CONTEXT', False)
READ_ONLY_ENABLED = get_settings('DB_MAILER_READ_ONLY_ENABLED', True)
UPLOAD_TO = get_settings('DB_MAILER_UPLOAD_TO', 'mail_files')
DEFAULT_CATEGORY = get_settings('DB_MAILER_DEFAULT_CATEGORY', None)
DEFAULT_FROM_EMAIL = get_settings('DB_MAILER_DEFAULT_FROM_EMAIL', None)
DEFAULT_PRIORITY = get_settings('DB_MAILER_DEFAULT_PRIORITY', 6)
TEMPLATES_PER_PAGE = get_settings('DB_MAILER_TEMPLATES_PER_PAGE', 20)
SEND_RETRY = get_settings('DB_MAILER_SEND_RETRY', 3)
SEND_RETRY_DELAY = get_settings('DB_MAILER_SEND_RETRY_DELAY', 300)
SEND_RETRY_DELAY_DIRECT = get_settings('DB_MAILER_SEND_RETRY_DELAY_DIRECT', 6)
SEND_MAX_TIME = get_settings('DB_MAILER_SEND_MAX_TIME', 30)
WSGI_AUTO_RELOAD = get_settings('DB_MAILER_WSGI_AUTO_RELOAD', False)
UWSGI_AUTO_RELOAD = get_settings('DB_MAILER_UWSGI_AUTO_RELOAD', False)
ENABLE_LOGGING = get_settings('DB_MAILER_ENABLE_LOGGING', True)
ADD_HEADER = get_settings('DB_MAILER_ADD_HEADER', False)
LOGS_EXPIRE_DAYS = get_settings('DB_MAILER_LOGS_EXPIRE_DAYS', 7)
ALLOWED_MODELS_ON_ADMIN = get_settings('DB_MAILER_ALLOWED_MODELS_ON_ADMIN', [
    'MailFromEmailCredential',
    'MailFromEmail',
    'MailCategory',
    'MailTemplate',
    'MailLog',
    'MailGroup',
    'Signal',
    'ApiKey',
    'MailBcc',
])
