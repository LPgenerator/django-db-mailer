from dbmail.backends.mail import Sender as SenderBase
from dbmail import import_module


class Sender(SenderBase):
    # you're custom provider will be defined here
    provider = 'dbmail.providers.slack.push'

    def _get_recipient_list(self, recipient):
        if isinstance(recipient, list):
            return recipient
        return map(lambda x: x.strip(), recipient.split(','))

    def _send(self):
        module = import_module(self.provider)
        for recipient in self._recipient_list:
            module.send(recipient, self._message)


class SenderDebug(Sender):
    def _send(self):
        self.debug('Message', self._message)


def send_db_slack(slug, *args, **kwargs):
    from dbmail import db_sender

    kwargs['backend'] = 'demo.custom_backends.slack'
    db_sender(slug, *args, **kwargs)
