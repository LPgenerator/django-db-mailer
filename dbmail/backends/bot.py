# -*- encoding: utf-8 -*-

from dbmail.defaults import BOT_PROVIDER, DEFAULT_BOT_FROM
from dbmail.backends.sms import (
    Sender as SenderBase,
    SenderDebug as SenderDebugBase
)
from dbmail.utils import clean_html
from dbmail import import_module


class Sender(SenderBase):
    provider = BOT_PROVIDER
    default_from = DEFAULT_BOT_FROM

    def _get_recipient_list(self, recipient):
        return self._email_to_list(recipient)

    def _send(self):
        module = import_module(self._provider)
        message = clean_html(self._message)
        for _id in self._recipient_list:
            module.send(_id, message, _from=self._from_email, **self._kwargs)


class SenderDebug(SenderDebugBase):
    pass
