# -*- encoding: utf-8 -*-

from dbmail.defaults import TTS_PROVIDER
from dbmail.backends.sms import SendMail as SendMailBase


class SendMail(SendMailBase):
    provider = TTS_PROVIDER
