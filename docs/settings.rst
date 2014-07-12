.. _settings:

Settings
========

``dbmail`` priority configuration:

.. code-block:: python

    DB_MAILER_PRIORITY_STEPS = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]


Install redis-server, and configure django-celery for use priority option::

    # pip install django-celery

    import djcelery

    INSTALLED_APPS += ('djcelery',)

    djcelery.setup_loader()

    BROKER_URL = 'redis://127.0.0.1:6379/5'

    PRIORITY_STEPS = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]

    DB_MAILER_PRIORITY_STEPS = PRIORITY_STEPS
    BROKER_TRANSPORT_OPTIONS = {
        'priority_steps': PRIORITY_STEPS,
    }


DB_MAILER_PRIORITY_STEPS == BROKER_TRANSPORT_OPTIONS['priority_steps']


Configure SMTP settings::

    EMAIL_HOST = 'smtp.gmail.com'
    EMAIL_PORT = 587
    EMAIL_HOST_USER = 'noreply@gmail.com'
    EMAIL_HOST_PASSWORD = 'your-password'
    EMAIL_USE_TLS = True
    DEFAULT_FROM_EMAIL = 'User <noreply@gmail.com>'


For minimize requests to database, configure caches::

    CACHES = {
        'default': {
            'BACKEND': 'django.core.cache.backends.memcached.PyLibMCCache',
        }
    }


Optionally, you may install and configure django-tinymce::

    # pip install django-tinymce

    TINYMCE_DEFAULT_CONFIG = {
        'plugins': "table,spellchecker,paste,searchreplace",
        'theme': "advanced",
        'cleanup_on_startup': True,
        'custom_undo_redo_levels': 10,
    }


For Django-1.4 define AUTH_USER_MODEL::

    AUTH_USER_MODEL = 'auth.User'
