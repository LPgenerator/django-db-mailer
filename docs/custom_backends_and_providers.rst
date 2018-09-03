Custom backends and providers
=============================


Double backend example
----------------------

A simple example of sending alerts by SMS and TTS.


.. code-block:: python


    from dbmail.backends.sms import Sender as SmsSender
    from dbmail.backends.tts import Sender as TtsSender


    class Sender(object):
        def __init__(self, *args, **kwargs):
            self.args = args
            self.kwargs = kwargs

        def send(self, is_celery=True):
            SmsSender(*self.args, **self.kwargs).send(is_celery)
            TtsSender(*self.args, **self.kwargs).send(is_celery)
            return 'OK'


    class SenderDebug(Sender):
        def send(self, is_celery=True):
            print(self.args)
            print(self.kwargs)
            print({'is_celery': is_celery})


    def send_double_notification(*args, **kwargs):
        from dbmail import db_sender

        kwargs['backend'] = 'demo.custom_backends.double'
        db_sender(*args, **kwargs)



Let's try:


.. code-block:: python


    from demo.custom_backends.double import send_double_notification

    send_double_notification('welcome', '+79031234567')



Slack backend example
---------------------

You're own backend, which send message to Slack channel.


.. code-block:: python


    from dbmail.backends.mail import Sender as SenderBase
    from dbmail import import_module


    class Sender(SenderBase):
        """
        Specify new backend when you want to change standard backends behavior
        More examples you can find at ./dbmail/backends directory
        """

        # you're custom provider will be defined here.
        # now we use standard provider
        provider = 'dbmail.providers.slack.push'

        # channels/recipients processing
        def _get_recipient_list(self, recipient):
            if isinstance(recipient, list):
                return recipient
            return map(lambda x: x.strip(), recipient.split(','))

        # send message
        def _send(self):
            module = import_module(self.provider)
            for recipient in self._recipient_list:
                module.send(recipient, self._message)


    class SenderDebug(Sender):
        """
        Print message to stdout when DEBUG is True
        """
        def _send(self):
            self.debug('Message', self._message)


    # helper function, which will be used on code
    def send_db_slack(slug, *args, **kwargs):
        from dbmail import db_sender

        kwargs['backend'] = 'demo.custom_backends.slack'
        db_sender(slug, *args, **kwargs)


Slack settings


.. code-block:: python


    SLACK_USERNAME = 'robot'
    SLACK_HOOCK_URL = 'https://hooks.slack.com/services/XXXXXXXXX/XXXXXXXXX/XXXXXXXXXXXXXXXXXXXXXXXX'
    SLACK_CHANNEL = 'main'


Let's try:


.. code-block:: python

    from demo.custom_backends.slack import send_db_slack

    send_db_slack('welcome', {'username': 'GoTLiuM'})



Own provider
------------

Create new file which will be implemented simple function below


.. code-block:: python

    def send(recipient, message, **kwargs):
        # some named args from send_db function
        custom_field = kwargs.pop('my_field', 'default value')
        ...
        # Some part of code, which will be send message over some protocol
        ...
        return True


Add necessary settings into settings.py


.. code-block:: python

    SOME_URL = '...'


Configure one of built-in backend to use your own provider


.. code-block:: python

    DB_MAILER_SMS_PROVIDER = 'apps.sms'
    DB_MAILER_TTS_PROVIDER = 'apps.tts'
    DB_MAILER_PUSH_PROVIDER = 'apps.push'


or write own function to use your provider


.. code-block:: python

    def send_over_own_provider(slug, *args, **kwargs):
        from dbmail import db_sender

        # can be one of built-in, or custom backend
        # kwargs['backend'] = 'dbmail.backends.sms'
        kwargs['provider'] = 'apps.sms'
        db_sender(slug, *args, **kwargs)
