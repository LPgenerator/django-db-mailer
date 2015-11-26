from dbmail.backends.mail import Sender as SenderBase
from dbmail import import_module


class Sender(SenderBase):
    # you're custom provider will be defined here
    provider = 'dbmail.providers.slack.push'

    def _send(self):
        import_module(self.provider).send('', self._message)


class SenderDebug(Sender):
    def _send(self):
        self.debug('Message', self._message)


def send_db_slack(slug, *args, **kwargs):
    from dbmail import db_sender

    kwargs['backend'] = 'demo.custom_backends.slack'
    db_sender(slug, '', *args, **kwargs)
