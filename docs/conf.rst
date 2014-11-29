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
    # and worker. On this constant you can specify which queue will be using
    # to send mail. For the different work you need specify workers on settings
    # with tasks routing or etc. By default django-db-mailer used default
    # queue. Do not forget run celery working with specified queue.
    DB_MAILER_CELERY_QUEUE = 'default'

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
