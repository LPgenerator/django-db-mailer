# -*- encoding: utf-8 -*-

import os

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
PUSH_QUEUE = get_settings('DB_MAILER_PUSH_QUEUE', CELERY_QUEUE)
SMS_QUEUE = get_settings('DB_MAILER_SMS_QUEUE', CELERY_QUEUE)
TTS_QUEUE = get_settings('DB_MAILER_TTS_QUEUE', CELERY_QUEUE)
BOT_QUEUE = get_settings('DB_MAILER_BOT_QUEUE', CELERY_QUEUE)
SIGNALS_QUEUE = get_settings('DB_MAILER_SIGNALS_QUEUE', CELERY_QUEUE)
SIGNALS_MAIL_QUEUE = get_settings('DB_MAILER_SIGNALS_MAIL_QUEUE', CELERY_QUEUE)
SUBSCRIPTION_QUEUE = get_settings('DB_MAILER_SUBSCRIPTION_QUEUE', CELERY_QUEUE)
TRACKING_QUEUE = get_settings('DB_MAILER_TRACKING_QUEUE', CELERY_QUEUE)
ENABLE_CELERY = get_settings('DB_MAILER_ENABLE_CELERY', True)
SHOW_CONTEXT = get_settings('DB_MAILER_SHOW_CONTEXT', False)
READ_ONLY_ENABLED = get_settings('DB_MAILER_READ_ONLY_ENABLED', True)
UPLOAD_TO = get_settings('DB_MAILER_UPLOAD_TO', 'mail_files')
DEFAULT_CATEGORY = get_settings('DB_MAILER_DEFAULT_CATEGORY', None)
DEFAULT_FROM_EMAIL = get_settings('DB_MAILER_DEFAULT_FROM_EMAIL', None)
DEFAULT_SMS_FROM = get_settings('DB_MAILER_DEFAULT_SMS_FROM', None)
DEFAULT_PUSH_FROM = get_settings('DB_MAILER_DEFAULT_PUSH_FROM', None)
DEFAULT_BOT_FROM = get_settings('DB_MAILER_DEFAULT_BOT_FROM', None)
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
    'MailLogTrack',
    'MailBaseTemplate',
    'MailSubscription',
    'MailLogException',
])
MAIL_SUBSCRIPTION_MODEL = get_settings(
    'DB_MAILER_MAIL_SUBSCRIPTION_MODEL', 'dbmail.models.MailSubscription')
AUTH_USER_MODEL = get_settings('AUTH_USER_MODEL', 'auth.User')
USE_CELERY_FOR_ADMIN_TEST = get_settings(
    'DB_MAILER_USE_CELERY_FOR_ADMIN_TEST', True)
CACHE_TTL = get_settings('DB_MAILER_CACHE_TIMEOUT', None)
ENABLE_USERS = get_settings('DB_MAILER_ENABLE_USERS', False)
SIGNAL_DEFERRED_DISPATCHER = get_settings(
    'DB_MAILER_SIGNAL_DEFERRED_DISPATCHER', 'celery')
SIGNAL_DB_DEFERRED_PURGE = get_settings(
    'DB_MAILER_SIGNAL_DB_DEFERRED_PURGE', True)

TRACK_ENABLE = get_settings('DB_MAILER_TRACK_ENABLE', True)
TRACK_USE_GEOIP2 = get_settings('DB_MAILER_TRACK_USE_GEOIP2', False)
TRACK_PIXEL = get_settings(
    'DB_MAILER_TRACK_PIXEL',
    [
        'image/gif',
        "\x47\x49\x46\x38\x39\x61\x01\x00\x01\x00\x80\x00"
        "\x00\xff\xff\xff\x00\x00\x00\x21\xf9\x04\x01\x00"
        "\x00\x00\x00\x2c\x00\x00\x00\x00\x01\x00\x01\x00"
        "\x00\x02\x02\x44\x01\x00\x3b"
    ]
)
TRACK_HTML = get_settings(
    'DB_MAILER_TRACK_HTML',
    '<table bgcolor="white"><tr><td><font size="-1" color="black">'
    '<img src="%(url)s" width="16" height="16" alt="" title="" border="0">'
    '</font></td></tr></table></center>')

BACKEND = get_settings('DB_MAILER_BACKEND', {
    'mail': 'dbmail.backends.mail',
    'tts': 'dbmail.backends.tts',
    'sms': 'dbmail.backends.sms',
    'push': 'dbmail.backends.push',
    'bot': 'dbmail.backends.bot',
})
_BACKEND = {v: k for k, v in BACKEND.items()}
BACKENDS_MODEL_CHOICES = get_settings('DB_MAILER_BACKENDS_MODEL_CHOICES', (
    (BACKEND.get('mail'), _('MailBox')),
    (BACKEND.get('push'), _('Push')),
    (BACKEND.get('sms'), _('SMS')),
    (BACKEND.get('tts'), _('TTS')),
    (BACKEND.get('bot'), _('BOT')),
))
SORTED_BACKEND_CHOICES = sorted(list(BACKEND.items()))

SMS_PROVIDER = get_settings(
    'DB_MAILER_SMS_PROVIDER', 'dbmail.providers.nexmo.sms')
TTS_PROVIDER = get_settings(
    'DB_MAILER_TTS_PROVIDER', 'dbmail.providers.nexmo.tts')
PUSH_PROVIDER = get_settings(
    'DB_MAILER_PUSH_PROVIDER', 'dbmail.providers.prowl.push')
BOT_PROVIDER = get_settings(
    'DB_MAILER_BOT_PROVIDER', 'dbmail.providers.telegram.bot')
MAIL_PROVIDER = get_settings('DB_MAILER_MAIL_PROVIDER', None)

SAFARI_PUSH_PATH = get_settings(
    'DB_MAILER_SAFARI_PUSH_PATH', settings.STATIC_ROOT or '.')

MESSAGE_HTML2TEXT = get_settings(
    'DB_MAILER_MESSAGE_HTML2TEXT', 'dbmail.utils')

IGNORE_BROWSE_APP = get_settings(
    'DB_MAILER_IGNORE_BROWSE_APP', [
        'south', 'dbmail', 'sessions', 'admin', 'djcelery',
        'auth', 'reversion', 'contenttypes'
    ])

MODEL_HTMLFIELD = get_settings(
    'DB_MAILER_MODEL_HTMLFIELD', 'dbmail.fields.HTMLField')
MODEL_SUBSCRIPTION_DATA_FIELD = get_settings(
    'DB_MAILER_MODEL_SUBSCRIPTION_DATA_FIELD', 'dbmail.fields.DataTextField')
APNS_PROVIDER_DEFAULT_ACTION = get_settings(
    'DB_MAILER_APNS_PROVIDER_DEFAULT_ACTION', 'Show')

DEBUG = settings.DEBUG and get_settings('DB_MAILER_DEBUG', False)
