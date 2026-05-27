from __future__ import annotations

import warnings
from http.client import HTTPSConnection
from json import dumps, loads
from urllib.parse import urlparse

from django.conf import settings


class GCMError(Exception):
    pass


def send(user, message, **kwargs):
    """
    Site: https://developers.google.com
    API: https://firebase.google.com/docs/cloud-messaging/migrate-v1
    Desc: Android notifications.

    Note: the legacy ``gcm/send`` HTTP endpoint and ``key=`` server-key
    auth were retired by Google on 2024-06-20. This shim keeps the
    legacy URL for installations still running on private gateways
    that proxy to the new FCM v1 API; greenfield projects should
    migrate to ``firebase-admin``-based dispatch.
    """
    warnings.warn(
        "dbmail.providers.google.android targets the legacy GCM HTTP "
        "API which Google retired on 2024-06-20. Migrate to FCM v1 "
        "(https://firebase.google.com/docs/cloud-messaging/migrate-v1) "
        "before 4.0; this provider will be reworked or removed.",
        DeprecationWarning,
        stacklevel=2,
    )

    headers = {"Content-type": "application/json", "Authorization": "key=" + kwargs.pop("gcm_key", settings.GCM_KEY)}

    hook_url = kwargs.pop("api_url", "https://fcm.googleapis.com/fcm/send")

    data = {
        "registration_ids": [user],
        "data": {
            "title": kwargs.pop("event"),
            "message": message,
        },
    }
    data["data"].update(kwargs)

    up = urlparse(hook_url)
    http = HTTPSConnection(up.netloc, timeout=10)
    try:
        http.request("POST", up.path, headers=headers, body=dumps(data))
        response = http.getresponse()

        if response.status != 200:
            raise GCMError(response.reason)

        body = response.read()
        if (loads(body).get("failure") or 0) > 0:
            raise GCMError(repr(body))
    finally:
        http.close()
    return True
