# -*- encoding: utf-8 -*-

from dbmail.backends.sms import SenderDebug as SenderDebugBase
from dbmail.backends.sms import Sender as SenderBase
from dbmail.defaults import TTS_PROVIDER


class Sender(SenderBase):
    provider = TTS_PROVIDER


class SenderDebug(SenderDebugBase):
    provider = TTS_PROVIDER
