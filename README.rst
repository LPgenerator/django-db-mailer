Django-Db-Mailer
================

.. image:: https://api.travis-ci.org/LPgenerator/django-db-mailer.png?branch=development
    :alt: Build Status
    :target: https://travis-ci.org/LPgenerator/django-db-mailer
.. image:: https://landscape.io/github/LPgenerator/django-db-mailer/master/landscape.svg
   :target: https://landscape.io/github/LPgenerator/django-db-mailer/master
   :alt: Code Health
.. image:: https://api.codacy.com/project/badge/grade/ad1442e15215494499ed08b80d4c41c5
    :target: https://www.codacy.com/app/gotlium/django-db-mailer
    :alt: Codacy
.. image:: https://img.shields.io/badge/python-2.7,3.4+,pypy,pypy3-blue.svg
    :alt: Python 2.7, 3.4+, pypy, pypy3
    :target: https://pypi.python.org/pypi/django-db-mailer/
.. image:: https://img.shields.io/pypi/v/django-db-mailer.svg
    :alt: Current version on PyPi
    :target: https://pypi.python.org/pypi/django-db-mailer/
.. image:: https://img.shields.io/pypi/dm/django-db-mailer.svg
    :alt: Downloads from PyPi
    :target: https://pypi.python.org/pypi/django-db-mailer/
.. image:: https://readthedocs.org/projects/django-db-mailer/badge/?version=latest
    :target: http://django-db-mailer.readthedocs.org/
    :alt: Documentation Status
.. image:: https://img.shields.io/badge/license-GPLv2-green.svg
    :target: https://pypi.python.org/pypi/django-db-mailer/
    :alt: License


Documentation available at `Read the Docs <http://django-db-mailer.readthedocs.org/>`_.


What's that
-----------
| Django module to easily send emails/push/sms/tts using django templates stored on database.
| From box you can use it with django-celery for send background messages.
| Also you have opportunity to create reports from logs by mail categories and slug.
| Groups with Recipients and send by model signal also available by default.
| Can be used without any depends from programming language as a external service.
| That app very simple to install and use on your projects.


Installation
------------

1. Using pip:

.. code-block:: bash

    $ pip install django-db-mailer

2. Add the ``dbmail`` application to ``INSTALLED_APPS`` in your settings file (usually ``settings.py``)
3. Sync database (``./manage.py syncdb`` or ``./manage.py migrate``).

**Important:** South 1.0 or greater is required to run migrations.


Mail API
--------

.. code-block:: python

    from dbmail.models import MailTemplate
    from dbmail import send_db_mail

    # New dbmail template
    MailTemplate.objects.create(
        name="Site welcome template",
        subject="[{{prefix}}] Welcome {{full_name}}!",
        message="Hi, {{username}}. Welcome to our site.",
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
            'signup_date': request.user.date_joined,
            'prefix': "DbMail",
        },

        # You can access to all model fields. For m2m and fk fields, you should use module_name
        MyModel.objects.get(pk=1),

        # Optional kwargs:
        # backend='dbmail.backends.mail',
        # provider='apps.utils.some.mail.provider',
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


Sms API
-------

.. code-block:: python

    from dbmail import send_db_sms


    send_db_sms(
        # slug which defined on db template
        slug='welcome',

        # recipient can be list, or str separated with comma or simple string
        # '+79031234567' or +79031234567, +79031234568, +79031234569' or
        # ['+79031234567', '+79031234568'] or string Mail group slug
        recipient='+79031234567',

        # All *args params will be accessible on template context
        {
            'username': request.user.username,
            'full_name': request.user.get_full_name(),
            'signup_date': request.user.date_joined
        },

        # You can access to all model fields. For m2m and fk fields, you should use module_name
        MyModel.objects.get(pk=1),

        # Optional kwargs:
        # backend='dbmail.backends.sms',
        # provider='dbmail.providers.nexmo.sms',
        # from_email='DBMail'
        # user=User.objects.get(pk=1),
        #
        # language='ru',
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



Text to speech API
------------------

.. code-block:: python

    from dbmail import send_db_tts


    send_db_tts(
        # slug which defined on db template
        slug='welcome',

        # recipient can be list, or str separated with comma or simple string
        # '+79031234567' or +79031234567, +79031234568, +79031234569' or
        # ['+79031234567', '+79031234568'] or string Mail group slug
        recipient='+79031234567',

        # All *args params will be accessible on template context
        {
            'username': request.user.username,
            'full_name': request.user.get_full_name(),
            'signup_date': request.user.date_joined
        },

        # You can access to all model fields. For m2m and fk fields, you should use module_name
        MyModel.objects.get(pk=1),

        # Optional kwargs:
        # backend='dbmail.backends.tts',
        # provider='dbmail.providers.nexmo.tts',
        # from_email='DBMail'
        # user=User.objects.get(pk=1),
        #
        # language='ru',
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


*Text to speech supported by default provider. But maybe not supported by your provider.*


Push notification API
---------------------

.. code-block:: python

    from dbmail import send_db_push


    send_db_push(
        # slug which defined on db template
        slug='welcome',

        # recipient can be list, or str separated with comma or simple string
        # '34cc3e5f0d2abf2ca0f9af170bd8cd2372a22f8a' or '34cc3e5f0d2abf2ca0f9af170bd8cd2372a22f8a, 34cc3e5f0d2abf2ca0f9af170bd8cd2372a22f8b' or
        # ['34cc3e5f0d2abf2ca0f9af170bd8cd2372a22f8a', '34cc3e5f0d2abf2ca0f9af170bd8cd2372a22f8b'] or string Mail group slug
        recipient='34cc3e5f0d2abf2ca0f9af170bd8cd2372a22f8c',

        # All *args params will be accessible on template context
        {
            'username': request.user.username,
            'full_name': request.user.get_full_name(),
            'signup_date': request.user.date_joined
        },

        # You can access to all model fields. For m2m and fk fields, you should use module_name
        MyModel.objects.get(pk=1),

        # Optional kwargs:
        # backend='dbmail.backends.push',
        # provider='dbmail.providers.prowl.push',
        # event='Server is down!',
        # from_email='ConsoleApp'
        # user=User.objects.get(pk=1),
        #
        # language='ru',
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


DBMail Backends
---------------
By default ``django-dbmail`` used 4 built-in backends (Mail/Sms/Tts/Push).
But nothing prevents to write your own backend to work with all that you want.


DBMail Providers
----------------
Battery have some built-in providers for most popular services, which will be
used without any dependencies with built-in backends.

**Push notifications for mobile apps:**

* Apple APNs/APNs2
* Google GCM
* Microsoft Tile/Toast/Raw
* BoxCar
* Parse

**Notifications for team:**

* Slack/Mattermost
* Boxcar
* Prowl
* Pushover
* PushAll

**Browser notifications:**

* Centrifugo
* PubNub
* BoxCar
* PushAll

**SMS notifications:**

* Nexmo
* Twilio
* IQsms
* SmsAero

**Mail notifications:**

* SendinBlue

*You can find providers settings on docs.*


Demo installation
-----------------

**Docker**

.. code-block:: bash

    $ git clone --depth 1 -b master https://github.com/LPgenerator/django-db-mailer.git db-mailer
    $ cd db-mailer
    $ docker build -t dbmail .
    $ docker run -it -d -p 8000:8000 --name dbmail dbmail
    $ docker exec -i -t dbmail /bin/bash
    $ cd /mailer/

**Vagrant**

.. code-block:: bash

    $ git clone --depth 1 -b master https://github.com/LPgenerator/django-db-mailer.git db-mailer
    $ cd db-mailer
    $ vagrant up --provider virtualbox
    $ vagrant ssh
    $ cd /mailer/


**OS X/Linux**


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
    $ redis-server >& /dev/null &
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


Open app in browser (login and password is admin/admin):

.. code-block:: bash

    $ xdg-open http://127.0.0.1:8000/admin/dbmail/ >& /dev/null || open http://127.0.0.1:8000/admin/dbmail/ >& /dev/null


Additional information
----------------------

**Revision**

For support template reversion, you can install ``django-reversion``.
Find information about compatibility with your Django versions `here <http://django-reversion.readthedocs.org/en/latest/django-versions.html>`_.

**Editor**

To enable editor, you may install and configure ``django-tinymce`` or ``django-ckeditor`` app.

**Theme**

``django-db-mailer`` supported from box ``django-grappelli`` and ``django-suit`` skin. Information about compatibility available `here <https://pypi.python.org/pypi/django-grappelli/2.5.3>`_.

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

**Postmark Django Backend**

Install ``python-postmark`` app via pip. Configure your settings:

.. code-block:: python

    POSTMARK_API_KEY = ''
    POSTMARK_SENDER = 'noreply@example.com'
    POSTMARK_TEST_MODE = False
    EMAIL_BACKEND = 'postmark.django_backend.EmailBackend'


**Amazon's Simple Email Service Django Backend**

Install ``django-ses`` app via pip. Configure your settings:

.. code-block:: python

    EMAIL_BACKEND = 'django_ses.SESBackend'

    # These are optional -- if they're set as environment variables they won't
    # need to be set here as well
    AWS_ACCESS_KEY_ID = 'YOUR-ACCESS-KEY-ID'
    AWS_SECRET_ACCESS_KEY = 'YOUR-SECRET-ACCESS-KEY'

    # Additionally, you can specify an optional region, like so:
    AWS_SES_REGION_NAME = 'us-east-1'
    AWS_SES_REGION_ENDPOINT = 'email.us-east-1.amazonaws.com'


*Note: You can use any backends designed as django email backend*

**Tracking**

.. code-block:: bash

    $ pip install httpagentparser django-ipware

For track information about user, or about mail is read, you must be enable logging, and enable tracking on settings.

**MJML**

MJML is a markup language designed to reduce the pain of coding a responsive email.
Install ``django-mjml`` app via pip and ``mjml`` via npm. And configure your settings:

.. code-block:: python

    INSTALLED_APPS = (
      ...,
      'mjml',
    )


**Older versions**

Very simple version of this app, available `here <https://github.com/LPgenerator/django-db-mailer/tree/1.0>`_.
That version do not include celery settings, bcc, api, mail settings, signals, mail groups and model browser.


**Notes**

All app features available only with ``django-celery`` and with ``Redis``.

.. code-block:: bash

    $ pip install redis hiredis django-celery



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
    $ curl -X POST http://127.0.0.1:8000/dbmail/api/ --data 'api_key=ZzriUzE&slug=welcome&recipient=root@local.host&backend=mail'

*API bandwidth is 1k+ rps on i7 2.3GHz*


Responsive transactional HTML email templates
---------------------------------------------
Fixtures with Base transactional HTML email templates was added into dbmail fixtures.
This templates was optimized for desktop clients, web clients, mobile clients, various devices, various providers.
Thanks for Mailgun Team. You can use it as default basic templates on your project.

.. code-block:: bash

    python manage.py load_dbmail_base_templates



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
.. image:: /screenshots/base_template_changelist.jpg
.. image:: /screenshots/subscriptions_change.jpg
.. image:: /screenshots/subscriptions_changelist.jpg


Compatibility
-------------
* Python: 2.7, pypy, 3.4, 3.5, pypy3
* Django: 1.4, 1.5, 1.6, 1.7, 1.8, 1.9
