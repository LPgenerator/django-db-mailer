# -*- encoding: utf-8 -*-

from django.utils.importlib import import_module
from django.conf import settings

from dbmail.defaults import SMS_PROVIDER, DEFAULT_SMS_FROM
from dbmail.backends.mail import Sender as SenderBase
from dbmail.utils import clean_html


class Sender(SenderBase):
    provider = SMS_PROVIDER
    default_from = DEFAULT_SMS_FROM

    def _get_from_email(self):
        if self._kwargs.get('from_email'):
            return self._kwargs.pop('from_email', None)
        elif not self._template.from_email:
            if self.default_from:
                return self.default_from
            else:
                return settings.DEFAULT_FROM_EMAIL.split('<')[0].strip()
        return self._template.from_email.email

    def _get_recipient_list(self, recipient):
        if not isinstance(recipient, list) and '+' not in recipient:
            return self._group_emails(recipient)
        return self._email_to_list(recipient)

    def _send(self):
        self._provider = self._provider or self.provider
        module = import_module(self._provider)
        message = clean_html(self._message)
        for phone in self._recipient_list:
            if self._from_email:
                module.send(
                    phone, message, sms_from=self._from_email, **self._kwargs)
            else:
                module.send(phone, message, **self._kwargs)
