# Django settings for demo project.

import os
import sys
import django

PROJECT_ROOT = os.path.normpath(os.path.dirname(__file__))

DEBUG = True
TEMPLATE_DEBUG = DEBUG

ADMINS = (
    ('root', 'root@local.host'),
)

MANAGERS = ADMINS

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(PROJECT_ROOT, 'db.sqlite'),
    }
}

ALLOWED_HOSTS = []

TIME_ZONE = 'Europe/Moscow'
LANGUAGE_CODE = 'en-us'
LANGUAGES = (
    ('ru', 'Russian'),
    ('en', 'English'),
)
USE_I18N = True
USE_L10N = True
USE_TZ = True

SITE_ID = 1

MEDIA_URL = '/media/'
STATIC_URL = '/static/'


STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
    'django.contrib.staticfiles.finders.DefaultStorageFinder',
)

SECRET_KEY = 'f969z_xc+^g*^gmt9oe7@og%kxd)54b!c!do)d7f2w2**f6%c0'

TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.Loader',
    'django.template.loaders.app_directories.Loader',
    'django.template.loaders.eggs.Loader',
)

TEMPLATE_CONTEXT_PROCESSORS = (
    'django.contrib.auth.context_processors.auth',
    'django.core.context_processors.request',
    'django.core.context_processors.static',
    "django.contrib.messages.context_processors.messages",
    "django.core.context_processors.i18n",
)

MIDDLEWARE_CLASSES = (
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
)

ROOT_URLCONF = 'demo.urls'

WSGI_APPLICATION = 'demo.wsgi.application'

TEMPLATE_DIRS = (
    os.path.join(PROJECT_ROOT, 'templates'),
)

INSTALLED_APPS = []

if 'test' not in sys.argv:
    INSTALLED_APPS += [
        'grappelli',
    ]

INSTALLED_APPS += [
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.admin',

    'dbmail',
]

if 'test' not in sys.argv:
    INSTALLED_APPS += [
        'django_extensions',
        'admin_jqueryui',
        'reversion',
        'reversion_compare',
        'djcelery',
        'tinymce',
        'rosetta',
        'south',
    ]

if django.VERSION >= (1, 7):
    DJ17_NOT_SUPPORTED_APPS = [
        'south', 'reversion', 'reversion_compare', 'tinymce']
    for app in DJ17_NOT_SUPPORTED_APPS:
        if app in INSTALLED_APPS:
            INSTALLED_APPS.remove(app)


LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'filters': {
        'require_debug_false': {
            '()': 'django.utils.log.RequireDebugFalse'
        }
    },
    'handlers': {
        'mail_admins': {
            'level': 'ERROR',
            'filters': ['require_debug_false'],
            'class': 'django.utils.log.AdminEmailHandler'
        }
    },
    'loggers': {
        'django.request': {
            'handlers': ['mail_admins'],
            'level': 'ERROR',
            'propagate': True,
        },
    }
}

ROSETTA_STORAGE_CLASS = 'rosetta.storage.SessionRosettaStorage'
ROSETTA_ENABLE_TRANSLATION_SUGGESTIONS = True


################ Django-Db-Mailer configuration ################
try:
    import djcelery

    djcelery.setup_loader()

    BROKER_URL = 'redis://127.0.0.1:6379/5'

    BROKER_TRANSPORT_OPTIONS = {
        'priority_steps': range(10),
    }

    CELERY_QUEUES = {
        'default': {
            "exchange": "default",
            "binding_key": "default",
        },
    }

    CELERY_IGNORE_RESULT = True
except ImportError:
    pass

TINYMCE_DEFAULT_CONFIG = {
    'plugins': "table,spellchecker,paste,searchreplace",
    'theme': "advanced",
    'cleanup_on_startup': True,
    'custom_undo_redo_levels': 10,
}

EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
DEFAULT_FROM_EMAIL = 'Django <no_reply@local.host>'

CACHES = {
    "default": {
        "BACKEND": "redis_cache.cache.RedisCache",
        "LOCATION": "127.0.0.1:6379:1",
    }
}

if 'test' is sys.argv:
    CACHES = {
        'default': {
            'BACKEND': 'django.core.cache.backends.filebased.FileBasedCache',
            'LOCATION': '/tmp/django_cache',
        }
    }

# DbMail settings
AUTH_USER_MODEL = 'auth.User'
DB_MAILER_SHOW_CONTEXT = True
DB_MAILER_WSGI_AUTO_RELOAD = False
DB_MAILER_UWSGI_AUTO_RELOAD = True

'''
# Translation settings
MODELTRANSLATION_DEFAULT_LANGUAGE = 'en'
MODELTRANSLATION_LANGUAGES = ('ru', 'en')
MODELTRANSLATION_TRANSLATION_FILES = (
    'dbmail.translation',
)
INSTALLED_APPS = ['modeltranslation'] + INSTALLED_APPS
'''

# For detect info about user
GEOIP_PATH = '/usr/share/GeoIP/'

############################################################

if django.VERSION[:2] < (1, 6):
    TEST_RUNNER = 'discover_runner.DiscoverRunner'

try:
    from local_settings import *

except ImportError:
    pass
