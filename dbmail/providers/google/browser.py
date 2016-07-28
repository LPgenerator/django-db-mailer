# -*- encoding: utf-8 -*-

from json import dumps, loads

from django.conf import settings
from pywebpush import WebPusher


class GCMError(Exception):
    pass


def send(subscription_info, message, **kwargs):
    """
    Site: https://developers.google.com
    API: https://developers.google.com/web/updates/2016/03/web-push-encryption
    Desc: Web Push notifications for Chrome and FireFox

    Installation:
    pip install 'pywebpush>=0.4.0'
    """

    payload = {
        "title": kwargs.pop("event"),
        "body": message,
    }
    payload.update(kwargs)

    wp = WebPusher(subscription_info)
    body = wp.send(
        dumps(payload), gcm_key=settings.GCM_KEY,
        ttl=kwargs.pop("ttl", 60))

    if loads(body.text).get("failure") > 0:
        raise GCMError(repr(body))
    return True
