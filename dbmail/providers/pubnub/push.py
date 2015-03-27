# -*- encoding: utf-8 -*-

from django.conf import settings
from Pubnub import Pubnub


class PushOverError(Exception):
    pass


def send(channel, message, **kwargs):
    """
    Site: http://www.pubnub.com/
    API: https://www.mashape.com/pubnub/pubnub-network
    Desc: real-time browser notifications

    Installation and usage:
    pip install -U pubnub
    Tests for browser notification http://127.0.0.1:8000/browser_notification/
    """

    pubnub = Pubnub(
        publish_key=settings.PUBNUB_PUB_KEY,
        subscribe_key=settings.PUBNUB_SUB_KEY,
        secret_key=settings.PUBNUB_SEC_KEY,
        ssl_on=kwargs.pop('ssl_on', False), **kwargs)
    return pubnub.publish(channel=channel, message={"text": message})
