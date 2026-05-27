"""Minimal Django settings used by the dbmail test suite."""

from __future__ import annotations

SECRET_KEY = "dbmail-tests"
DEBUG = False
USE_TZ = True

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
    }
}

INSTALLED_APPS = [
    "django.contrib.contenttypes",
    "django.contrib.auth",
    "django.contrib.admin",
    "django.contrib.sessions",
    "django.contrib.sites",
    "django.contrib.messages",
    "dbmail",
]

MIDDLEWARE: list[str] = []

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    }
]

SITE_ID = 1
ROOT_URLCONF = "dbmail.urls"
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        "LOCATION": "dbmail-tests",
    }
}

# Celery — synchronous in tests.
CELERY_TASK_ALWAYS_EAGER = True
CELERY_TASK_EAGER_PROPAGATES = True
CELERY_BROKER_URL = "memory://"

# Provider placeholders so module-level settings access does not blow up.
APNS_GW_HOST = "gateway.push.apple.com"
APNS_GW_PORT = 2195
APNS_KEY_FILE = "/tmp/dbmail-test-key"
APNS_CERT_FILE = "/tmp/dbmail-test-cert"
SAFARI_PUSH_PATH = "/tmp/dbmail-safari-push"

HTTP_KEY = ""
PROWL_APP = "dbmail-tests"

# dbmail-specific.
DB_MAILER_API_RATE_LIMIT = (60, 60)
DB_MAILER_API_HMAC_SECRET = ""
DB_MAILER_ENABLE_CELERY = False
