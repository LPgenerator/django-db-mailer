# -*- encoding: utf-8 -*-

from django.conf import settings


def get_settings(key, default):
    return getattr(settings, key, default)


PRIORITY_STEPS = get_settings('DB_MAILER_PRIORITY_STEPS', range(10))
RETRY_INTERVAL = get_settings('DB_MAILER_RETRY_INTERVAL', 3)
