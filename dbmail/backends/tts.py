# -*- encoding: utf-8 -*-

from dbmail.defaults import TTS_PROVIDER
from dbmail.backends.sms import Sender as SenderBase


class Sender(SenderBase):
    provider = TTS_PROVIDER
