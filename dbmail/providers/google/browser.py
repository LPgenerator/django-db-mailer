from __future__ import annotations

from json import dumps, loads

from django.conf import settings


class GCMError(Exception):
    pass


def send(reg_id, message, **kwargs):
    """
    Site: https://developers.google.com
    API: https://developers.google.com/web/updates/2016/03/web-push-encryption
    Desc: Web Push notifications for Chrome and FireFox.

    Requires ``pywebpush>=2``. Install via the ``[webpush]`` extra:
    ``pip install "django-db-mailer[webpush]"``.
    """
    from pywebpush import WebPusher

    subscription_info = kwargs.pop("subscription_info")
    ttl = kwargs.pop("ttl", 60)

    payload = {"title": kwargs.pop("event"), "body": message, "url": kwargs.pop("push_url", None)}
    payload.update(kwargs)

    wp = WebPusher(subscription_info)
    response = wp.send(dumps(payload), gcm_key=settings.GCM_KEY, ttl=ttl)

    if not response.ok or (response.text and (loads(response.text).get("failure") or 0) > 0):
        raise GCMError(response.text)
    return True
