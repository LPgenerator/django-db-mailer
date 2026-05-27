from __future__ import annotations

import warnings
from http.client import HTTPSConnection
from json import dumps, loads

from django.conf import settings

from dbmail import get_version


class ParseComError(Exception):
    pass


def send(device_id, description, **kwargs):
    """
    Site: http://parse.com
    API: https://www.parse.com/docs/push_guide#scheduled/REST

    Note: Parse.com was shut down by Facebook on 2017-01-28. This
    provider remains for backwards compatibility and will be removed
    in dbmail 4.0. Migrate to Firebase Cloud Messaging (FCM) or APNs.
    """
    warnings.warn(
        "dbmail.providers.parse_com is deprecated: Parse.com was shut "
        "down by Facebook on 2017-01-28. This provider will be removed "
        "in dbmail 4.0; migrate to FCM (dbmail.providers.google.android) "
        "or APNs (dbmail.providers.apple.apns2).",
        DeprecationWarning,
        stacklevel=2,
    )
    headers = {
        "X-Parse-Application-Id": settings.PARSE_APP_ID,
        "X-Parse-REST-API-Key": settings.PARSE_API_KEY,
        "User-Agent": "DBMail/%s" % get_version(),
        "Content-type": "application/json",
    }

    data = {
        "where": {
            "user_id": device_id,
        },
        "data": {"alert": description, "title": kwargs.pop("event")},
    }

    _data = kwargs.pop("data", None)
    if _data is not None:
        data.update(_data)

    http = HTTPSConnection(kwargs.pop("api_url", "api.parse.com"), timeout=10)
    try:
        http.request("POST", "/1/push", headers=headers, body=dumps(data))
        response = http.getresponse()

        if response.status != 200:
            raise ParseComError(response.reason)

        body = loads(response.read())
        if body.get("error"):
            raise ParseComError(body["error"])
    finally:
        http.close()
    return True
