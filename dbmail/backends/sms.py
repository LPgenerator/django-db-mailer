# -*- encoding: utf-8 -*-

from django.utils.importlib import import_module
from django.utils.html import strip_tags
from django.conf import settings

from dbmail.defaults import SMS_PROVIDER, DEFAULT_SMS_FROM
from dbmail.backends.mail import Sender as SenderBase


class Sender(SenderBase):
    provider = SMS_PROVIDER

    def _get_from_email(self):
        if self._kwargs.get('from_email'):
            return self._kwargs.pop('from_email', None)
        elif not self._template.from_email:
            if DEFAULT_SMS_FROM:
                return DEFAULT_SMS_FROM
            else:
                return settings.DEFAULT_FROM_EMAIL.split('<')[0].strip()
        return self._template.from_email.email

    def _get_recipient_list(self, recipient):
        if not isinstance(recipient, list) and '+' not in recipient:
            return self._group_emails(recipient)
        return self._email_to_list(recipient)

    def _send(self):
        module = import_module(self.provider)
        message = strip_tags(self._message)
        for phone in self._recipient_list:
            if self._from_email:
                module.send(
                    phone, message, sms_from=self._from_email, **self._kwargs)
            else:
                module.send(phone, message, **self._kwargs)
