.. _conf:

App settings
============

``django-db-mailer`` has some configuration which can be configured on project:


.. code-block:: python

    # Default priority steps for admin.
    # For more information about configure celery redis ``quasi-priorities``
    # you can find here http://celery.readthedocs.org/en/latest/whatsnew-3.0.html#redis-priority-support
    DB_MAILER_PRIORITY_STEPS = (
        (0, _("High")),
        (3, _("Medium")),
        (6, _("Low")),
        (9, _("Deferred")),
    )

    # Best practice is use mail messages with priorities with different queue
    # and worker. On this constants you can specify which queue will be using
    # to send msg. For the different work you need specify workers on settings
    # with tasks routing or etc. By default django-db-mailer used default
    # queue. Do not forget run celery working with specified queue.
    DB_MAILER_CELERY_QUEUE = 'default'
    DB_MAILER_PUSH_QUEUE = 'default'
    DB_MAILER_SMS_QUEUE = 'default'
    DB_MAILER_TTS_QUEUE = 'default'
    DB_MAILER_SUBSCRIPTION_QUEUE = 'default'

    # By default celery is enabled. If djcelery is not on INSTALLED_APPS,
    # this option is useless. When djcelery on INSTALLED_APPS, and you want
    # disable it for some reason, you can change this constant.
    # It very helpful for local development.
    DB_MAILER_ENABLE_CELERY = True

    # Show mail context into console. It very helpful for local development.
    DB_MAILER_SHOW_CONTEXT = False

    # Disable edit slug and notes on the admin. For production.
    DB_MAILER_READ_ONLY_ENABLED = True

    # Where attachments will be stored after uploading
    DB_MAILER_UPLOAD_TO = 'mail_files'

    # Default category on the admin
    DB_MAILER_DEFAULT_CATEGORY = None

    # Default email on the admin
    DB_MAILER_DEFAULT_FROM_EMAIL = None

    # Default priority for new templates
    DB_MAILER_DEFAULT_PRIORITY = 6

    # List per page on the admin template page
    DB_MAILER_TEMPLATES_PER_PAGE = 20

    # How much retries when error occurring by default
    DB_MAILER_SEND_RETRY = 1

    # Default delay before retry attempt
    DB_MAILER_SEND_RETRY_DELAY = 300

    # If celery is not used, this delay will be used to retry
    DB_MAILER_SEND_RETRY_DELAY_DIRECT = 3

    # Hard limit for send mail
    DB_MAILER_SEND_MAX_TIME = 30

    # Reload on the fly after Signal models will be changed
    DB_MAILER_WSGI_AUTO_RELOAD = False
    DB_MAILER_UWSGI_AUTO_RELOAD = False

    # You can disable logging emails by default.
    # This option override settings defined on the db templates
    DB_MAILER_ENABLE_LOGGING = True

    # Add app header. Very helpful for test app on production
    DB_MAILER_ADD_HEADER = False

    # Logs expire days for management command
    DB_MAILER_LOGS_EXPIRE_DAYS = 7

    # Models which will be show on the admin.
    # Helpful when all features are not required
    DB_MAILER_ALLOWED_MODELS_ON_ADMIN = [
        'MailFromEmailCredential',
        'MailFromEmail',
        'MailCategory',
        'MailTemplate',
        'MailLog',
        'MailGroup',
        'Signal',
        'ApiKey',
        'MailBcc',
    ]

    # If you are using celery, and have a big mail queue,
    # and admin can not be wait, when he receive test email,
    # you can set False, and mail will be send without queue
    DB_MAILER_USE_CELERY_FOR_ADMIN_TEST = True

    # When inside invalidation not invalidate templates, you can use this
    # constant, for automatically invalidation after defined seconds.
    # By default cache invalidate only when admin update some templates.
    DB_MAILER_CACHE_TIMEOUT = None

    # We are strongly recommended use a different queue for signals, mail and mail on signals
    # Because on standard mail queue you will use priorities
    # Big queues with countdown will constantly interfere and will be break, if priority steps are to be used on current queue
    DB_MAILER_SIGNALS_QUEUE = "default"
    DB_MAILER_SIGNALS_MAIL_QUEUE = "default"

    # For pending and very long task, you must use a database instead of the celery queues
    DB_MAILER_SIGNAL_DEFERRED_DISPATCHER = 'celery'

    # Remove database long tasks after execution
    DB_MAILER_SIGNAL_DB_DEFERRED_PURGE = True

    # Enable/Disable tracking functionality.
    # If tracking is enabled, Logging must be enabled to.
    # DbMail urls must be configured.
    # Site framework must configured and installed.
    DB_MAILER_TRACK_ENABLE = True

    # Tracking image content and mime type
    DB_MAILER_TRACK_PIXEL = [
        'image/gif',
        "\x47\x49\x46\x38\x39\x61\x01\x00\x01\x00\x80\x00"
        "\x00\xff\xff\xff\x00\x00\x00\x21\xf9\x04\x01\x00"
        "\x00\x00\x00\x2c\x00\x00\x00\x00\x01\x00\x01\x00"
        "\x00\x02\x02\x44\x01\x00\x3b"
    ]

    # Html code for inject into message for tracking
    DB_MAILER_TRACK_HTML = '<table bgcolor="white"><tr><td><font size="-1" color="black"><img src="%(url)s" width="16" height="16" alt="" title="" border="0"></font></td></tr></table></center>'

    # Default backend for sending mail/sms/tts. You can redefine standard backend for implement your custom logic.
    DB_MAILER_BACKEND' = {
        'mail': 'dbmail.backends.mail',
        'tts': 'dbmail.backends.tts',
        'sms': 'dbmail.backends.sms',
    }

    # Default providers for sms and text to speech. If you want use different providers, you can write simple function to do it. Look to examples at dbmail.providers.nexmo.sms.
    DB_MAILER_SMS_PROVIDER = 'dbmail.providers.nexmo.sms'
    DB_MAILER_TTS_PROVIDER = 'dbmail.providers.nexmo.tts'
    DB_MAILER_PUSH_PROVIDER = 'dbmail.providers.prowl.push'

    # By default real api call is using.
    # For log all requests to stdout - use True flag.
    # Django DEBUG must be enabled.
    DB_MAILER_DEBUG = False

    # Default SMS from
    DB_MAILER_DEFAULT_SMS_FROM = None

    # Default Push notification from
    DB_MAILER_DEFAULT_PUSH_FROM = None

    # Apps which will be ignored on model browser
    DB_MAILER_IGNORE_BROWSE_APP = [
        'dbmail', 'sessions', 'admin', 'djcelery',
        'auth', 'reversion', 'contenttypes'
    ]

    # Function for transform html to text
    DB_MAILER_MESSAGE_HTML2TEXT = 'dbmail.utils'

    # Path to HTMLField class.
    DB_MAILER_MODEL_HTMLFIELD = 'django.db.models.TextField'

    # Path to MailSubscription class.
    DB_MAILER_MAIL_SUBSCRIPTION_MODEL = 'dbmail.models.MailSubscription'

    # You can use any backends designed as django email backend
    # Example:
    # - django.core.mail.backends.console.EmailBackend
    # - postmark.django_backend.EmailBackend
    # - django_ses.SESBackend and etc
    # By default:
    EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'

    # Subscription data field
    DB_MAILER_MODEL_SUBSCRIPTION_DATA_FIELD = 'dbmail.fields.DataTextField'

    # Default apns action
    DB_MAILER_APNS_PROVIDER_DEFAULT_ACTION = 'Show'


Providers settings
==================

Apple APNs
----------

.. code-block:: python

    # Apple APNs provider settings
    APNS_GW_HOST = 'gateway.sandbox.push.apple.com'  # or gateway.push.apple.com on production
    APNS_GW_PORT = 2195
    APNS_CERT_FILE = 'cert.pem'                      # required. convert your p12 to pem
    APNS_KEY_FILE = None

    # Apple APNs via HTTP/2 protocol
    APNS_GW_HOST = 'api.development.push.apple.com'  # or api.push.apple.com on production
    APNS_GW_PORT = 443                               # or alternative 2197
    APNS_CERT_FILE = 'cert.pem'                      # required. convert your p12 to pem


Google GCM
----------

.. code-block:: python

    # Android GCM provider settings
    GCM_KEY = 'XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX'


Microsoft MPNs
--------------

.. code-block:: python

    # Windows MPNs provider settings
    WP_CERT_FILE = None


Centrifugo
----------

.. code-block:: python

    # Centrifugo provider settings
    CENTRIFUGO_TOKEN = 'secret'
    CENTRIFUGO_API = 'https://centrifugo.herokuapp.com/api/'


Nexmo
-----

.. code-block:: python

    # nexmo.com (TTS and SMS)
    NEXMO_USERNAME = ''
    NEXMO_PASSWORD = ''
    NEXMO_FROM = 'DBMail'
    NEXMO_LANG = 'en-us'


Prowl
-----

.. code-block:: python

    # prowlapp.com provider settings
    PROWL_APP = 'DBMail'


Parse
-----

.. code-block:: python

    # parse.com provider settings
    PARSE_APP_ID = ""
    PARSE_API_KEY = ""


PushOver
--------

.. code-block:: python

    # pushover.net provider settings
    PUSHOVER_TOKEN = ""
    PUSHOVER_APP = "DBMail"


PubNub
------

.. code-block:: python

    # pubnub.com provider settings
    PUBNUB_PUB_KEY = ""
    PUBNUB_SUB_KEY = ""
    PUBNUB_SEC_KEY = ""


Twilio
------

.. code-block:: python

    # twilio.com provider settings
    TWILIO_ACCOUNT_SID = ""
    TWILIO_AUTH_TOKEN = ""
    TWILIO_FROM = ""


IQSms
-----

.. code-block:: python

    # iqsms.ru provider settings
    IQSMS_API_LOGIN = ""
    IQSMS_API_PASSWORD = ""
    IQSMS_FROM = ""


SmsAero
-------

.. code-block:: python

    # smsaero.ru
    SMSAERO_LOGIN = ""
    SMSAERO_MD5_PASSWORD = ""
    SMSAERO_FROM = ""


Slack/Mattermost
----------------

.. code-block:: python

    # slack.com / mattermost.org
    SLACK_USERNAME = 'Robot'
    SLACK_HOOCK_URL = 'https://hooks.slack.com/services/XXXXXXXXX/XXXXXXXXX/XXXXXXXXXXXXXXXXXXXXXXXX'
    SLACK_CHANNEL = 'main'


PushAll
-------

.. code-block:: python

    # pushall.ru
    PUSHALL_API_KEYS = {
        'default': {
            'title': 'AppName',
            'key': 'KEY',
            'id': 'ID',
            'priority': '1',
        }
    }


SmsBliss
--------

.. code-block:: python

    # smsbliss.ru/
    SMSBLISS_API_URL = 'http://api.smsbliss.net/messages/v2/send.json'
    SMSBLISS_LOGIN = ''
    SMSBLISS_PASSWORD = ''
    SMSBLISS_FROM = 'DbMail'
