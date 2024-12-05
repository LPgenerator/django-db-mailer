.. _usage:

Usage
=====

To use ``django-db-mailer`` on the your project - Add and Configure mail templates on the admin page.


Mail API
--------
SendMail API with all available options:

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

        # ...
        # another named arguments, which supported by specified backend
        # ...
    )

*``slug`` and ``recipient`` is not a named arguments.*

*For track information about read - add dbmail into urls.*


SMS API
-------

.. code-block:: python

    from dbmail import send_db_sms


    send_db_sms(
        # slug which defined on db template
        slug='welcome',

        # recipient can be list, or str separated with comma or simple string
        # '+79031234567' or '+79031234567, +79031234568, +79031234569' or
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



TTS API
-------

.. code-block:: python

    from dbmail import send_db_tts


    send_db_tts(
        # slug which defined on db template
        slug='welcome',

        # recipient can be list, or str separated with comma or simple string
        # '+79031234567' or '+79031234567, +79031234568, +79031234569' or
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


PUSH API
--------

.. code-block:: python

    from dbmail import send_db_push


    send_db_push(
        # slug which defined on db template
        slug='welcome',

        # recipient can be list, or str separated with comma or simple string
        # '+34cc3e5f0d2abf2ca0f9af170bd8cd2372a22f8a' or '34cc3e5f0d2abf2ca0f9af170bd8cd2372a22f8a, 34cc3e5f0d2abf2ca0f9af170bd8cd2372a22f8b' or
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
        '', re_path(r'^dbmail/', include('dbmail.urls')),
    )


And send email from bash using ``curl``:

.. code-block:: bash

    $ apt-get install curl || brew install curl
    $ curl -X POST http://127.0.0.1:8000/dbmail/api/ --data 'api_key=ZzriUzE&slug=welcome&recipient=root@local.host'


or sms:

.. code-block:: bash

    $ curl -X POST http://127.0.0.1:8000/dbmail/api/ --data 'api_key=ZzriUzE&slug=welcome&recipient=%2B79031234567&backend=sms'


*API bandwidth is 1k+ rps on i7 2.3GHz*


DB template
-----------
Simple example to create template from shell:

.. code-block:: python

    from dbmail.models import MailTemplate

    # Create new dbmail template.
    MailTemplate.objects.create(
        name="Site welcome template",
        subject="[{{prefix}}] Welcome {{full_name}}",
        message="Hi, {{username}}. Welcome to our site.",
        slug="welcome",
        is_html=True,
    )


Subscription API
----------------
Full stack (multiple) notification example for django.contrib.auth.models.users

.. code-block:: python

    from dbmail.models import MailSubscription
    from dbmail import send_db_subscription

    # Email notification
    MailSubscription.objects.create(
        user_id=1,  # you can omit user_id if user not registered
        backend="dbmail.backends.mail",
        is_checked=True,
        address="user1@example.com"
    )

    # Push notification
    MailSubscription.objects.create(
        user_id=1,
        backend="dbmail.backends.push",
        start_hour="08:00",
        end_hour="20:00",
        is_checked=True,
        defer_at_allowed_hours=True,
        address="d30NSrq10aO0hsyHDZ3"
    )

    # Send notification to all devices
    send_db_subscription('welcome', 1)


If you want send notification for all subscribers, you can omit user_id

.. code-block:: python

    from dbmail.models import MailSubscription
    from dbmail import send_db_subscription

    # Subscribe nonexistent user for email notification
    MailSubscription.objects.create(
        is_checked=True,
        address="user2@example.com"
    )

    # Subscribe nonexistent user for push notification
    MailSubscription.objects.create(
        backend="dbmail.backends.push",
        is_checked=True,
        address="d30NSrq10aO0hsyHDZ4"
    )

    # Send notification to all available users (all devices)
    send_db_subscription('welcome')


Send notification for all active users which registered at last 3 days ago (all devices):

.. code-block:: python

    from datetime import datetime, timedelta
    from dbmail import send_db_subscription

    send_db_subscription('welcome', None, {
        'user__is_active': 1,
        'user__date_joined__gte': datetime.now() - timedelta(days=3)
    })


Send confirmation email message:

.. code-block:: python

    from dbmail.models import MailSubscription
    from django.core.signing import dumps

    # subscribe user
    sub_obj = MailSubscription.objects.create(
        is_checked=False,
        address="user3@example.com"
    )

    # create hash code for confirmation
    kwargs['hash_code'] = dumps({'pk': sub_obj.pk})

    # send message (create MailTemplate)
    MailSubscription.send_confirmation_link(
        slug='subs-confirmation', **kwargs
    )


Create your own view for confirmation:

.. code-block:: python

    from dbmail.models import MailSubscription
    from django.core.signing import loads

    def confirmation(hash_code):
        data = loads(hash_code)
        sub_obj = MailSubscription.objects.get(pk=data['pk'])
        sub_obj.is_checked = True
        sub_obj.save()

