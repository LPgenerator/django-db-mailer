# -*- encoding: utf-8 -*-

from dbmail.defaults import DEFAULT_PUSH_FROM, PUSH_PROVIDER
from dbmail.backends.sms import Sender as SenderBase
from dbmail.utils import clean_html
from dbmail import import_module


class Sender(SenderBase):
    provider = PUSH_PROVIDER
    default_from = DEFAULT_PUSH_FROM

    def _get_recipient_list(self, recipient):
        if not isinstance(recipient, list):
            email_list = self._group_emails(recipient)
            if email_list:
                return email_list
        return self._email_to_list(recipient)

    def _send(self):
        self._provider = self._provider or self.provider
        module = import_module(self._provider)
        message = clean_html(self._message)
        for phone in self._recipient_list:
            options = self._kwargs.copy()
            options['event'] = self._kwargs.pop('event', self._subject)
            if self._from_email:
                options['app'] = self._from_email
            module.send(phone, message, **options)


class SenderDebug(Sender):
    def _send(self):
        self.debug('Provider', self._provider or self.provider)
        self.debug('Message', clean_html(self._message))
        self.debug('Recipients', self._recipient_list)
        self.debug('Event', self._subject)
        self.debug('App', self._from_email)
