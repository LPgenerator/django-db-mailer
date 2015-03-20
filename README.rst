Django-Db-Mailer
----------------

.. image:: https://api.travis-ci.org/LPgenerator/django-db-mailer.png?branch=development
    :alt: Build Status
    :target: https://travis-ci.org/LPgenerator/django-db-mailer
.. image:: https://pypip.in/v/django-db-mailer/badge.png
    :alt: Current version on PyPi
    :target: https://crate.io/packages/django-db-mailer/
.. image:: https://pypip.in/d/django-db-mailer/badge.png
    :alt: Downloads from PyPi
    :target: https://crate.io/packages/django-db-mailer/
.. image:: https://readthedocs.org/projects/django-db-mailer/badge/?version=latest
    :target: http://django-db-mailer.readthedocs.org/
    :alt: Documentation Status

Documentation available at `Read the Docs <http://django-db-mailer.readthedocs.org/>`_.


What's that
-----------
| Django module to easily send emails using django templates stored on database.
| From box you can use it with django-celery for send background messages.
| Also you have opportunity to create reports from logs by mail categories and slug.
| Groups with Recipients and send by model signal also available by default.
| That app very simple to install and use on your projects.


Installation
------------

1. Using pip:

.. code-block:: bash

    $ pip install django-db-mailer

2. Add the ``dbmail`` application to ``INSTALLED_APPS`` in your settings file (usually ``settings.py``)
3. Sync database (``./manage.py syncdb`` or ``./manage.py migrate``).

**Important:** South 1.0 or greater is required to run migrations.


Development installation
------------------------

1. Using pip:

.. code-block:: bash

    $ pip install git+https://github.com/LPgenerator/django-db-mailer.git@development


Usage examples
--------------

.. code-block:: python

    from dbmail.models import MailTemplate
    from dbmail import send_db_mail

    # New dbmail template
    MailTemplate.objects.create(
        name="Site welcome template",
        subject="Welcome",
        message="Welcome to our site. We are glad to see you.",
        slug="welcome",
        is_html=False,
    )

    # Send message with created template
    send_db_mail(
        # slug which defined on db template
        slug='welcome',

        # recipient can be list, or str separated with comma or simple string
        # 'user1@example.com' or 'user1@example.com, user2@example.com' or
        # ['user1@example.com', 'user2@example.com'] or string Mail group slug
        recipient='user1@example.com',

        # All *args params will be accessible on template context
        {
            'username': request.user.username,
            'full_name': request.user.get_full_name(),
            'signup_date': request.user.date_joined
        },

        # You can access to all model fields. For m2m and fk fields, you should use module_name
        MyModel.objects.get(pk=1),

        # Optional kwargs:
        # from_email='from@example.com'
        # cc=['cc@example.com'],
        # bcc=['bcc@example.com'],
        # user=User.objects.get(pk=1),
        #
        # language='ru',
        #
        # attachments=[(filename, content, mimetype)],
        # files=['hello.jpg', 'world.png'],
        # headers={'Custom-Header':'Some value'},
        #
        # queue='default',
        # retry_delay=300,
        # max_retries=3,
        # retry=True,
        # time_limit=30,
        # send_after=60,
        #
        # use_celery=True,
    )


Local demo installation
-----------------------

.. code-block:: bash

    $ sudo apt-get install -y virtualenvwrapper redis-server git python-dev libxml2-dev libxslt-dev zlib1g-dev || brew install pyenv-virtualenvwrapper redis git
    $ source /usr/share/virtualenvwrapper/virtualenvwrapper.sh || source /usr/local/bin/virtualenvwrapper.sh
    $ mkvirtualenv db-mailer
    $ workon db-mailer
    $ git clone --depth 1 https://github.com/LPgenerator/django-db-mailer.git db-mailer
    $ cd db-mailer
    $ python setup.py develop
    $ cd demo
    $ pip install -r requirements.txt
    $ python manage.py syncdb --noinput
    $ python manage.py migrate --noinput
    $ python manage.py createsuperuser --username admin --email admin@local.host
    $ python manage.py runserver >& /dev/null &
    $ python manage.py celeryd -Q default >& /dev/null &


Open Shell:

.. code-block:: bash

    $ python manage.py shell_plus --print-sql


Create new template:

.. code-block:: python

    from dbmail.models import MailTemplate
    from dbmail import send_db_mail

    MailTemplate.objects.create(
        name="Site welcome template",
        subject="Welcome",
        message="Welcome to our site. We are glad to see you.",
        slug="welcome",
        is_html=False,
    )


Try to send test email with created template (without celery):

.. code-block:: python

    send_db_mail('welcome', 'user@example.com', use_celery=False)


Send email using celery:

.. code-block:: python

    send_db_mail('welcome', 'user@example.com')


Check mail logs:

.. code-block:: python

    from pprint import pprint
    from django.forms.models import model_to_dict
    from dbmail.models import MailLog

    pprint([model_to_dict(obj) for obj in MailLog.objects.all()])


Open app on browser:

.. code-block:: bash

    $ xdg-open http://127.0.0.1:8000/admin/dbmail/ >& /dev/null || open http://127.0.0.1:8000/admin/dbmail/ >& /dev/null


Additional information
----------------------

**Revision**

For support template reversion, you can install ``django-reversion``.
Find information about compatibility with your Django versions `here <http://django-reversion.readthedocs.org/en/latest/django-versions.html>`_.

**Editor**

To enable editor, you may install and configure ``django-tinymce`` app.

**Theme**

``django-db-mailer`` supported from box ``django-grappelli`` skin. Information about compatibility available `here <https://pypi.python.org/pypi/django-grappelli/2.5.3>`_.

**Queue**

Install and configure ``django-celery`` for background message sending with priorities. You can find celery settings examples on demo project.
We recommended to use ``django-celery-mon`` with ``django-celery`` for monitoring celery and supervisor processes.

**Premailer**

For turns CSS blocks into style attributes, you can install ``premailer`` from PyPi.

**Translation**

For use different language on your mail templates, install ``django-modeltranslation`` or ``grappelli-modeltranslation``.
Add into settings.py:

.. code-block:: python

    MODELTRANSLATION_DEFAULT_LANGUAGE = 'en'
    MODELTRANSLATION_LANGUAGES = ('ru', 'en')
    MODELTRANSLATION_TRANSLATION_FILES = (
        'dbmail.translation',
    )
    INSTALLED_APPS = ('modeltranslation',) + INSTALLED_APPS
    # INSTALLED_APPS = ('grappelli', 'grappelli_modeltranslation', 'modeltranslation',) + INSTALLED_APPS


Update dbmail fields:

.. code-block:: bash

    $ ./manage.py sync_translation_fields --noinput

**Postmark backend**

Install ``python-postmark`` app via pip. Configure your settings:

.. code-block:: python

    POSTMARK_API_KEY = ''
    POSTMARK_SENDER = 'noreply@example.com'
    POSTMARK_TEST_MODE = False
    EMAIL_BACKEND = 'postmark.django_backend.EmailBackend'


**Tracking**:

.. code-block:: bash

    $ pip install httpagentparser django-ipware

For track information about user, or about mail is read, you must be enable logging, and enable tracking on settings.


**Older versions**

Very simple version of this app, available `here <https://github.com/LPgenerator/django-db-mailer/tree/1.0>`_.
That version do not include celery settings, bcc, api, mail settings, signals, mail groups and model browser.


**Notes**

All app features available only with ``django-celery`` and with ``Redis``.


External API usage
------------------

.. code-block:: python

    from dbmail.models import ApiKey

    ApiKey.objects.create(name='Test', api_key='ZzriUzE')


.. code-block:: bash

    $ pip install httpie
    $ http -f POST http://127.0.0.1:8000/dbmail/api/ api_key=ZzriUzE slug=welcome recipient=root@local.host data='{"name": "Ivan", "age": 20}'
        or
    $ apt-get install curl || brew install curl
    $ curl -X POST http://127.0.0.1:8000/dbmail/api/ --data 'api_key=ZzriUzE&slug=welcome&recipient=root@local.host'


Publications
------------
* `Установка и использование с примерами на русском <http://habrahabr.ru/post/253445/>`_.
* `Completely installation and usage with examples. Translated by Google <http://translate.google.com/translate?hl=en&sl=ru&tl=en&u=http://habrahabr.ru/post/253445/>`_.


Screenshots
-----------

.. image:: /screenshots/template_edit.jpg
.. image:: /screenshots/templates_changelist.jpg
.. image:: /screenshots/template_log_changelist.jpg
.. image:: /screenshots/template_log_view.jpg
.. image:: /screenshots/group_change.jpg
.. image:: /screenshots/signal_edit.jpg
.. image:: /screenshots/signals_changelist.jpg
.. image:: /screenshots/apps_view.jpg
.. image:: /screenshots/apps_browse_vars.jpg
.. image:: /screenshots/smtp_changelist.jpg
.. image:: /screenshots/apikey_changelist.jpg
.. image:: /screenshots/bcc_changelist.jpg
.. image:: /screenshots/template_compare.jpg
.. image:: /screenshots/tracking_edit.jpg


Compatibility
-------------

* Python: 2.6, 2.7
* Django: 1.4, 1.5, 1.6, 1.7


Contributing
------------

Please use development branch before adding code modifications.