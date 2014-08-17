What's that
-----------
| Django module to easily send emails using django templates stored on database.
| From box you can use it with django-celery for send background messages.
| Also you have opportunity create reports from logs by mail categories and slug.
| That app very simple to install and use on your projects.


Installation:
-------------

1. Using pip:

.. code-block:: bash

    $ pip install django-db-mailer

2. Add the ``dbmail`` application to ``INSTALLED_APPS`` in your settings file (usually ``settings.py``)
3. Sync database (``./manage.py syncdb``)


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
        # slug was defined on db template
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
    )


Local demo installation
-----------------------

.. code-block:: bash

    $ sudo apt-get install virtualenvwrapper
    $ mkvirtualenv django-db-mailer
    $ git clone https://github.com/LPgenerator/django-db-mailer.git
    $ cd django-db-mailer
    $ python setup.py develop
    $ cd demo
    $ pip install -r requirements.txt
    $ python manage.py syncdb
    $ python manage.py migrate
    $ python manage.py runserver


Additional information
----------------------

**Revision**

| For support template revisions, you can install ``django-reversion``.
| Find information about compatibility with your Django versions `here <http://django-reversion.readthedocs.org/en/latest/django-versions.html>`_.


**Editor**

To enable editor, you may install and configure ``django-tinymce`` app.

**Theme**

``django-db-mailer`` supported from box ``django-grappelli`` skin. Information about compatibility available `here <https://pypi.python.org/pypi/django-grappelli/2.5.3>`_.

**Queue**

Install and configure ``django-celery`` for background message sending with priorities. You can find celery settings examples on demo project.

**Note**

All app features available only with ``django-celery`` and with ``Redis``.



External API usage
------------------

.. code-block:: bash

    $ pip install httpie
    $ http -f POST http://127.0.0.1:8000/dbmail/api/ api_key=ZzriUzE slug=welcome recipient=root@local.host data='{"name": "Ivan", "age": 20}'
        or
    $ curl -X POST http://127.0.0.1:8000/dbmail/api/ --data 'api_key=ZzriUzE&slug=welcome&recipient=root@local.host'


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


Compatibility:
-------------
* Python: 2.6, 2.7
* Django: 1.4, 1.5, 1.6
