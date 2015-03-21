# -*- encoding: utf-8 -*-

from django.utils.importlib import import_module
from django.utils.html import strip_tags

from dbmail.defaults import DEFAULT_PUSH_FROM, PUSH_PROVIDER
from dbmail.backends.sms import Sender as SenderBase


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
        module = import_module(self.provider)
        message = strip_tags(self._message)
        for phone in self._recipient_list:
            options = self._kwargs.copy()
            options['event'] = self._kwargs.pop('event', self._subject)
            if self._from_email:
                options['app'] = self._from_email
            module.send(phone, message, **options)
