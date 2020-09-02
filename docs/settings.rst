.. _settings:

Settings
========

Required Settings
-----------------

For minimize requests to database, configure django caches:

.. code-block:: bash

    $ pip install redis django-pylibmc
        # or
    $ pip install redis django-redis

.. code-block:: python

    # settings.py
    CACHES = {
        # Memcached
        'default': {
            'BACKEND': 'django.core.cache.backends.memcached.PyLibMCCache',
        },
        # or Redis
        "default": {
            'BACKEND': 'redis_cache.cache.RedisCache',
            'LOCATION': '127.0.0.1:6379:2',
        },
        # or Memory
        "default": {
            'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
            'LOCATION': 'unique-snowflake'
        },
    }

*Note: App do not work without caches*


Configure project default SMTP settings::

    # settings.py
    EMAIL_HOST = 'smtp.gmail.com'
    EMAIL_PORT = 587
    EMAIL_HOST_USER = 'noreply@gmail.com'
    EMAIL_HOST_PASSWORD = 'your-password'
    EMAIL_USE_TLS = True
    DEFAULT_FROM_EMAIL = 'User <noreply@gmail.com>'


Also you can configure smtp options for dbmail on the admin interface. But maybe other apps,
like ``django-registration`` is used default project settings.


Optional Settings
-----------------

Install ``redis-server``, and configure ``django-celery`` for use priorities and scheduler:

.. code-block:: bash

    $ pip install redis django-celery


.. code-block:: python

    # settings.py

    import djcelery
    import sys

    INSTALLED_APPS += ('djcelery',)

    BROKER_URL = 'redis://127.0.0.1:6379/1'

    CELERY_ACKS_LATE = True
    CELERYD_PREFETCH_MULTIPLIER = 1

    # use priority steps only for mail queue
    if 'mail_messages' in sys.argv:
        BROKER_TRANSPORT_OPTIONS = {
            'priority_steps': list(range(10)),
        }

    CELERY_TASK_SERIALIZER = 'pickle'
    CELERY_DEFAULT_QUEUE = 'default' # use mail_messages, if workers is divided

    djcelery.setup_loader()


.. code-block:: bash

    $ python manage.py celeryd --loglevel=debug -Q default
    $ python manage.py celeryd --loglevel=info -Q mail_messages -n mail_messages # divide workers and queues on production


*Note: Do not forget define on command line queue name.*


``django-db-mailer`` can work without any third-party apps, but if you want to use all
available app features and send emails on the background with priorities and scheduler,
you need configure some apps, which will be pretty for your project and your clients.


**Templates Revision**:

.. code-block:: bash

    $ pip install django-reversion

.. code-block:: python

    # settings.py
    INSTALLED_APPS += ('reversion',)

Find information about compatibility with your Django versions `here <http://django-reversion.readthedocs.org/en/latest/django-versions.html>`_.


**Templates Compare Revision**:

.. code-block:: bash

    $ pip install django-reversion-compare diff-match-patch

.. code-block:: python

    # settings.py
    INSTALLED_APPS += ('reversion', 'reversion_compare',)


``django-reversion-compare`` is not compatible at this time with Django 1.4+,
but you can override ``django-reversion-compare`` templates on your project templates,
and app will be work with Django 1.4+.


**Editor**:

.. code-block:: bash

    $ pip install django-tinymce
    # OR
    $ pip install django-ckeditor

.. code-block:: python

    # settings.py
    INSTALLED_APPS += ('tinymce',)
    TINYMCE_DEFAULT_CONFIG = {
        'plugins': "table,spellchecker,paste,searchreplace",
        'theme': "advanced",
        'cleanup_on_startup': True,
        'custom_undo_redo_levels': 10,
    }
    # urls.py
    urlpatterns += patterns(
        '', url(r'^tinymce/', include('tinymce.urls')),
    )


**Premailer**:

.. code-block:: bash

    $ pip install premailer

That's all what you need. App for turns CSS blocks into style attributes. Very pretty for cross-clients html templates.


**Theme**:

.. code-block:: bash

    $ pip install django-grappelli

``django-db-mailer`` supported from box ``django-grappelli`` and ``django-suit`` skin. Information about compatibility available `here <https://pypi.python.org/pypi/django-grappelli/2.5.3>`_.


**Translation Support**:

.. code-block:: bash

    $ pip install django-modeltranslation

.. code-block:: python

    # settings.py
    MODELTRANSLATION_DEFAULT_LANGUAGE = 'en'
    MODELTRANSLATION_LANGUAGES = ('ru', 'en')
    MODELTRANSLATION_TRANSLATION_FILES = (
        'dbmail.translation',
    )
    INSTALLED_APPS = ('modeltranslation',) + INSTALLED_APPS

    # If you are using django-grappelli, add grappelli_modeltranslation to the settings
    INSTALLED_APPS = (
        'grappelli',
        'grappelli_modeltranslation',
        'modeltranslation',
    ) + INSTALLED_APPS

.. code-block:: bash

    $ ./manage.py collectstatic


Update dbmail fields:

.. code-block:: bash

    $ ./manage.py sync_translation_fields --noinput


**Tracking**:

.. code-block:: bash

    $ pip install httpagentparser django-ipware geoip2

If you use Django 1.8, you should install `geoip` package instead of `geoip2`.


Add url patterns into urls.py:

.. code-block:: python

    urlpatterns += patterns(
        '', url(r'^dbmail/', include('dbmail.urls')),
    )


Enable tracking and logging on settings:

.. code-block:: python

    DB_MAILER_TRACK_ENABLE = True
    DB_MAILER_ENABLE_LOGGING = True


For track information about user, or about mail is read, you must be enable logging, and enable tracking on settings.
Tracking templates must be HTML, not TXT. Celery workers must be launched, if celery is enabled.
Django ``sites`` framework must be configured properly and have a real domain name record.
``LibGeoIP`` and ``MaxMind`` database must be installed and properly configured.
To debug, open raw message and you can see html which specified on ``DB_MAILER_TRACK_HTML``.
