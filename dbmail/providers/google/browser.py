# -*- encoding: utf-8 -*-

from json import dumps, loads

from django.conf import settings
from pywebpush import WebPusher


class GCMError(Exception):
    pass


def send(reg_id, message, **kwargs):
    """
    Site: https://developers.google.com
    API: https://developers.google.com/web/updates/2016/03/web-push-encryption
    Desc: Web Push notifications for Chrome and FireFox

    Installation:
    pip install 'pywebpush>=0.4.0'
    """

    subscription_info = kwargs.pop('subscription_info')

    payload = {
        "title": kwargs.pop("event"),
        "body": message,
        "url": kwargs.pop("push_url", None)
    }
    payload.update(kwargs)

    wp = WebPusher(subscription_info)
    response = wp.send(
        dumps(payload), gcm_key=settings.GCM_KEY,
        ttl=kwargs.pop("ttl", 60))

    if not response.ok or (
            response.text and loads(response.text).get("failure") > 0):
        raise GCMError(response.text)
    return True
