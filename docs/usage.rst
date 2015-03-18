Usage
=====

To use ``django-db-mailer`` on the your project - Add and Configure mail templates on the admin page.


High level API
--------------
Send mail API with comments for all available options:

.. code-block:: python

    from dbmail import send_db_mail

    send_db_mail(
        # slug - which defined on db template
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

        #######################################################################
        ### Optional kwargs:
        #######################################################################
        from_email='from@example.com',
        cc=['cc@example.com'],
        bcc=['bcc_1@example.com', 'bcc_2@example.com'],

        # For store on mail logs
        user=User.objects.get(pk=1),

        # Current language code, which selected by user
        language='ru',

        # This options is documented on the Django docs
        attachments=[(filename, content, mimetype)],
        files=['hello.jpg', 'world.png'],
        headers={'Custom-Header':'Some value'},

        # For working with different queue, you can specify queue name on the settings, or on option
        queue='default',

        # Time for retry failed send. Working with celery only
        retry_delay=300,

        # Max retries, when sending is failed
        max_retries=3,

        # You can disable retry function
        retry=True,

        # Hard limit on seconds
        time_limit=30,

        # Postpone send email for specified seconds
        send_after=60,

        # You can disable celery for debug messages, or when error is occurred,
        # and email can not be delivered by celery.
        # Or some part of your app run on instance, where celery is not used.
        use_celery=True,
    )

*For track information about read - add dbmail into urls.*


Web API
-------
You can use this app with different languages. For example on mobile apps,
bash or some part of another languages without smtp access for notification & etc.

At first create API key for your app (you can do it from browser):

.. code-block:: python

    from dbmail.models import ApiKey

    ApiKey.objects.create(name='Test', api_key='ZzriUzE')


Add urls route:

.. code-block:: python

    # urls.py
    urlpatterns += patterns(
        '', url(r'^dbmail/', include('dbmail.urls')),
    )


And send email from bash using ``curl``:

.. code-block:: bash

    $ apt-get install curl || brew install curl
    $ curl -X POST http://127.0.0.1:8000/dbmail/api/ --data 'api_key=ZzriUzE&slug=welcome&recipient=root@local.host'


DB template
-----------
Simple example to create template from the shell:

.. code-block:: python

    from dbmail.models import MailTemplate

    # Create new dbmail template.
    MailTemplate.objects.create(
        name="Site welcome template",
        subject="Welcome",
        message="Welcome to our site. We are glad to see you.",
        slug="welcome",
        is_html=False,
    )
