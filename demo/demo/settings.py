# Django settings for demo project.

import os
import sys
import django
import dbmail

PROJECT_ROOT = os.path.normpath(os.path.dirname(__file__))

DEBUG = True

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

ALLOWED_HOSTS = ['*']

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

MEDIA_ROOT = os.path.join(PROJECT_ROOT, 'media')
STATIC_ROOT = os.path.join(PROJECT_ROOT, 'static')

MEDIA_URL = '/media/'
STATIC_URL = '/static/'

STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
    'django.contrib.staticfiles.finders.DefaultStorageFinder',
)

SECRET_KEY = 'f969z_xc+^g*^gmt9oe7@og%kxd)54b!c!do)d7f2w2**f6%c0'

TEMPLATES = [{
    'BACKEND': 'django.template.backends.django.DjangoTemplates',
    'DIRS': [],
    'APP_DIRS': True,
    'OPTIONS': {
        'context_processors': [
            'django.template.context_processors.debug',
            'django.template.context_processors.request',
            'django.contrib.auth.context_processors.auth',
            'django.contrib.messages.context_processors.messages',

        ],
    },
}]

MIDDLEWARE = (
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
)

ROOT_URLCONF = 'demo.urls'

WSGI_APPLICATION = 'demo.wsgi.application'

INSTALLED_APPS = []

if 'test' not in sys.argv:
    INSTALLED_APPS += [
        # 'suit',
        'grappelli.dashboard',
        'grappelli',
        'sslserver',
    ]

INSTALLED_APPS += [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    'dbmail',
]

if 'test' not in sys.argv:
    INSTALLED_APPS += [
        'django_extensions',
        'reversion',
        'reversion_compare',
        'djcelery',
        'ckeditor',
        # 'rosetta',
    ]

    if 'grappelli' not in INSTALLED_APPS:
        INSTALLED_APPS += ['admin_jqueryui']


LOGGING = {
    'version': 1,
    'disable_existing_loggers': True,
    'root': {
        'level': 'WARNING',
        'handlers': ['console'],
    },
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
        },
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            # 'formatter': 'verbose'
        }
    },
    'loggers': {
        'django.request': {
            'handlers': ['console'],
            'level': 'ERROR',
            'propagate': True,
        }
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
    CELERY_ACCEPT_CONTENT = ['pickle']
    REDIS_CONNECT_RETRY = True
except ImportError:
    pass

TINYMCE_DEFAULT_CONFIG = {
    'plugins': "table,spellchecker,paste,searchreplace",
    'theme': "advanced",
    'cleanup_on_startup': True,
    'custom_undo_redo_levels': 10,
}

CKEDITOR_UPLOAD_PATH = os.path.join(MEDIA_ROOT, 'uploads')

CKEDITOR_CONFIGS = {
    'default': {
        'toolbar': None,
        'height': 300,
        'width': '100%',
        'allowedContent': True,
    },
}

SUIT_CONFIG = {
    'ADMIN_NAME': 'Django DB Mailer v.%s' % dbmail.get_version(),
    'SEARCH_URL': '',
    'MENU': (
        {'app': 'dbmail', 'label': 'DBMailer', 'icon': 'icon-align-justify'},
    )
}

GRAPPELLI_ADMIN_TITLE = 'Django DB Mailer v.%s' % dbmail.get_version()
GRAPPELLI_INDEX_DASHBOARD = 'demo.dashboard.DBMailerDashboard'

EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
DEFAULT_FROM_EMAIL = 'Django <no_reply@local.host>'


if 'test' not in sys.argv:
    CACHES = {
        "default": {
            "BACKEND": "django_redis.cache.RedisCache",
            "LOCATION": "127.0.0.1:6379",
        }
    }
else:
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

if django.VERSION < (1, 6):
    TEST_RUNNER = 'discover_runner.DiscoverRunner'

try:
    from local_settings import *

except ImportError:
    pass
