.. _signals:

Signals
=======

Signals on database is a native Django signals.

Available variables for rules on Signals:

.. code-block:: html

    {{ date }} - current date
    {{ date_time }} - current datetime
    {{ site }} - current site
    {{ domain }} - current site domain
    {{ old_instance }} - old instance for pre_save
    {{ current_instance }} - available when Update model state is enabled
    {{ instance }} - instance from received signal
    {{ ... }} - all instance fields as vars

When all signals was configured, you need to reload your wsgi application.
Auto-reloading can be configured on settings by WSGI_AUTO_RELOAD/UWSGI_AUTO_RELOAD.
But if you launch application on several instances, do it manually.

**Note:** Don't use a big intervals, if deferred tasks on queue more than 3-4k. It can crash a celery worker.

For deferred tasks best way is a crontab command + database queue.
You can add ``DB_MAILER_SIGNAL_DEFERRED_DISPATCHER = 'database'`` into project settings,
and call crontab command ``send_dbmail_deferred_signal``.


Sending signals
---------------

.. code-block:: python

    from dbmail.exceptions import StopSendingException
    from dbmail.signals import pre_send, post_send
    from dbmail.backends.sms import Sender as SmsSender


    def check_balance(*args, **kwargs):
        # "if" condition is unnecessary due to the way we connect signal to handler
        if kwargs['instance']._backend.endswith('sms'):
            balance = ...
            if balance == 0:
                raise StopSendingException

    def decrease_balance(*args, **kwargs):
        # decrease user balance
        pass


    pre_send.connect(check_balance, sender=SmsSender)
    post_send.connect(decrease_balance, sender=SmsSender)


When you want transmit some **kwargs to signal, you can use `signals_kwargs`.

.. code-block:: python

    from dbmail import send_db_mail

    send_db_mail(
        'welcome', 'user@example.com',
        signals_kwargs={'user': User.objects.get(pk=1)}, use_celery=False
    )

