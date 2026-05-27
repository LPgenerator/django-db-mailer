"""Django settings for the django-db-mailer demo project.

Adapted (not stripped) for Django 4.2 / 5.2 / 6.0 and Python 3.10+.
The historical set of admin extensions (Grappelli, CKEditor, Reversion,
Rosetta, debug-toolbar, extensions) is preserved as documentation of
how dbmail integrates with each one. Only physically dead packages
(djcelery, admin-jqueryui, sslserver, redis-cache, bootstrap-static,
tornado, pyzmq, MySQL-python) are removed.

Sensitive configuration is read from environment variables; the
``.env`` loading is handled by python-dotenv outside this file.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

import dbmail

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parent
BASE_DIR = PROJECT_ROOT.parent

# ---------------------------------------------------------------------------
# Core flags
# ---------------------------------------------------------------------------
TESTING = "test" in sys.argv or "pytest" in sys.modules
DEBUG = os.environ.get("DJANGO_DEBUG", "1") == "1"

SECRET_KEY = os.environ.get(
    "DJANGO_SECRET_KEY",
    # Insecure fallback used only for local development; production
    # MUST set DJANGO_SECRET_KEY explicitly.
    "demo-insecure-do-not-use-in-production",
)

ALLOWED_HOSTS = os.environ.get("DJANGO_ALLOWED_HOSTS", "localhost,127.0.0.1,::1").split(",")

ADMINS = (("root", "root@local.host"),)
MANAGERS = ADMINS

# ---------------------------------------------------------------------------
# Database (sqlite by default; DATABASE_URL overrides via dj-database-url)
# ---------------------------------------------------------------------------
DATABASES: dict = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": str(PROJECT_ROOT / "db.sqlite"),
    }
}
_DATABASE_URL = os.environ.get("DATABASE_URL")
if _DATABASE_URL:
    try:
        import dj_database_url

        DATABASES["default"] = dj_database_url.parse(_DATABASE_URL, conn_max_age=600)
    except ImportError:
        pass  # dj-database-url is in [demo] extras; SQLite fallback is OK


DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# ---------------------------------------------------------------------------
# Localization
# ---------------------------------------------------------------------------
TIME_ZONE = os.environ.get("TIME_ZONE", "UTC")
LANGUAGE_CODE = "en-us"
LANGUAGES = (
    ("ru", "Russian"),
    ("en", "English"),
)
USE_I18N = True
USE_TZ = True
SITE_ID = 1

# ---------------------------------------------------------------------------
# Static & media
# ---------------------------------------------------------------------------
STATIC_URL = "/static/"
STATIC_ROOT = str(PROJECT_ROOT / "static")
MEDIA_URL = "/media/"
MEDIA_ROOT = str(PROJECT_ROOT / "media")

STATICFILES_FINDERS = (
    "django.contrib.staticfiles.finders.FileSystemFinder",
    "django.contrib.staticfiles.finders.AppDirectoriesFinder",
)

# Django 4.2+ STORAGES dict (replaces STATICFILES_STORAGE / DEFAULT_FILE_STORAGE).
STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {
        "BACKEND": (
            "whitenoise.storage.CompressedManifestStaticFilesStorage"
            if not DEBUG
            else "django.contrib.staticfiles.storage.StaticFilesStorage"
        ),
    },
}

# ---------------------------------------------------------------------------
# Templates
# ---------------------------------------------------------------------------
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    }
]

# ---------------------------------------------------------------------------
# Middleware
# ---------------------------------------------------------------------------
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]
if DEBUG and not TESTING:
    try:
        import debug_toolbar  # noqa: F401

        MIDDLEWARE.insert(
            MIDDLEWARE.index("django.middleware.common.CommonMiddleware") + 1,
            "debug_toolbar.middleware.DebugToolbarMiddleware",
        )
    except ImportError:
        pass

# ---------------------------------------------------------------------------
# URLconf / WSGI / ASGI
# ---------------------------------------------------------------------------
ROOT_URLCONF = "demo.urls"
WSGI_APPLICATION = "demo.wsgi.application"
ASGI_APPLICATION = "demo.asgi.application"

# ---------------------------------------------------------------------------
# Installed apps
# ---------------------------------------------------------------------------
# Historical set of admin extensions is preserved (see plan/06-demo-project.md).
# Each one is gated by an importability check so a missing package does not
# blow up the demo — useful while operators upgrade incrementally.

INSTALLED_APPS: list[str] = []


def _add_if_installed(name: str) -> None:
    try:
        __import__(name.replace("-", "_"))
    except ImportError:
        return
    INSTALLED_APPS.append(name)


# Grappelli must be listed before django.contrib.admin.
if not TESTING:
    _add_if_installed("grappelli.dashboard")
    _add_if_installed("grappelli")

INSTALLED_APPS += [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.sites",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "dbmail",
    "demo.apps.DemoConfig",
]

if not TESTING:
    for app in (
        "django_extensions",
        "reversion",
        "reversion_compare",
        "ckeditor",
        "rosetta",
        "debug_toolbar",
        "tinymce",
    ):
        _add_if_installed(app)

# debug_toolbar wants INTERNAL_IPS.
INTERNAL_IPS = ["127.0.0.1", "::1"]

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "filters": {
        "require_debug_false": {"()": "django.utils.log.RequireDebugFalse"},
    },
    "formatters": {
        "verbose": {
            "format": "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "verbose",
        },
        "mail_admins": {
            "level": "ERROR",
            "filters": ["require_debug_false"],
            "class": "django.utils.log.AdminEmailHandler",
        },
    },
    "root": {
        "level": "INFO",
        "handlers": ["console"],
    },
    "loggers": {
        "django.request": {
            "handlers": ["console", "mail_admins"],
            "level": "ERROR",
            "propagate": False,
        },
        "dbmail": {
            "handlers": ["console"],
            "level": os.environ.get("DBMAIL_LOG_LEVEL", "INFO"),
            "propagate": False,
        },
    },
}

# ---------------------------------------------------------------------------
# Caches
# ---------------------------------------------------------------------------
_REDIS_URL = os.environ.get("REDIS_URL")
if _REDIS_URL and not TESTING:
    CACHES = {
        "default": {
            "BACKEND": "django_redis.cache.RedisCache",
            "LOCATION": _REDIS_URL,
        }
    }
else:
    CACHES = {
        "default": {
            "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
            "LOCATION": "demo-locmem",
        }
    }

# ---------------------------------------------------------------------------
# Email backend (console for development)
# ---------------------------------------------------------------------------
EMAIL_BACKEND = os.environ.get("EMAIL_BACKEND", "django.core.mail.backends.console.EmailBackend")
DEFAULT_FROM_EMAIL = os.environ.get("DEFAULT_FROM_EMAIL", "Django <no_reply@local.host>")

# ---------------------------------------------------------------------------
# Celery (5.x, namespaced)
# ---------------------------------------------------------------------------
CELERY_BROKER_URL = os.environ.get("CELERY_BROKER_URL", "redis://127.0.0.1:6379/0")
CELERY_RESULT_BACKEND = os.environ.get("CELERY_RESULT_BACKEND", "redis://127.0.0.1:6379/1")
CELERY_BROKER_TRANSPORT_OPTIONS = {"priority_steps": list(range(10))}
CELERY_TASK_ACKS_LATE = True
CELERY_TASK_TIME_LIMIT = 30
CELERY_TASK_SOFT_TIME_LIMIT = 25
CELERY_WORKER_PREFETCH_MULTIPLIER = 1
CELERY_TASK_IGNORE_RESULT = True
CELERY_ACCEPT_CONTENT = ["json"]
CELERY_TASK_SERIALIZER = "json"
CELERY_RESULT_SERIALIZER = "json"
CELERY_TIMEZONE = TIME_ZONE
CELERY_TASK_ALWAYS_EAGER = TESTING

# ---------------------------------------------------------------------------
# CKEditor / TinyMCE
# ---------------------------------------------------------------------------
CKEDITOR_UPLOAD_PATH = os.path.join(MEDIA_ROOT, "uploads")
CKEDITOR_CONFIGS = {
    "default": {
        "toolbar": None,
        "height": 300,
        "width": "100%",
        "allowedContent": True,
    },
}
# Silence the bundled-CKEditor-4 security warning. CKEditor 4.x is kept
# in the demo for historical compatibility; migration to CKEditor 5 via
# django-ckeditor-5 is scheduled for 3.1.0 (see CHANGELOG).
SILENCED_SYSTEM_CHECKS = ["ckeditor.W001"]

TINYMCE_DEFAULT_CONFIG = {
    "menubar": False,
    "plugins": "advlist autolink lists link table searchreplace",
    "toolbar": ("undo redo | bold italic underline | link table | bullist numlist | removeformat"),
    "height": 300,
}

# ---------------------------------------------------------------------------
# Grappelli
# ---------------------------------------------------------------------------
GRAPPELLI_ADMIN_TITLE = "Django DB Mailer v.%s" % dbmail.get_version()
GRAPPELLI_INDEX_DASHBOARD = "demo.dashboard.DBMailerDashboard"

# ---------------------------------------------------------------------------
# Rosetta
# ---------------------------------------------------------------------------
ROSETTA_STORAGE_CLASS = "rosetta.storage.SessionRosettaStorage"
ROSETTA_ENABLE_TRANSLATION_SUGGESTIONS = True

# ---------------------------------------------------------------------------
# django-db-mailer settings
# ---------------------------------------------------------------------------
DB_MAILER_SHOW_CONTEXT = True
DB_MAILER_WSGI_AUTO_RELOAD = False
DB_MAILER_UWSGI_AUTO_RELOAD = False

# Cache-based per-key rate limit (count, seconds). 0 disables.
DB_MAILER_API_RATE_LIMIT = (60, 60)

# Optional HMAC body signature on the API endpoint.
DB_MAILER_API_HMAC_SECRET = os.environ.get("DB_MAILER_API_HMAC_SECRET", "")

# GeoIP2 database (used by MailLogTrack.detect_geo).
GEOIP_PATH = os.environ.get("GEOIP_PATH", "/usr/share/GeoIP/")

# ---------------------------------------------------------------------------
# Local overrides
# ---------------------------------------------------------------------------
try:
    from local_settings import *  # noqa: F403
except ImportError:
    pass
