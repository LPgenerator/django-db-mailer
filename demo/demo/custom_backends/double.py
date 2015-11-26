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
