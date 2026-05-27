from __future__ import annotations

import warnings
from http.client import HTTPSConnection
from urllib.parse import urlencode

from dbmail import get_version
from dbmail.providers._compat import from_unicode


class BoxcarError(Exception):
    pass


def send(token, title, **kwargs):
    """
    Site: https://boxcar.io/
    API: http://help.boxcar.io/knowledgebase/topics/48115-boxcar-api

    Note: Boxcar service has been end-of-life since ~2016. This
    provider remains for backwards compatibility and will be removed
    in dbmail 4.0. Migrate to APNs (dbmail.providers.apple.apns2)
    for iOS or FCM (dbmail.providers.google.android) for Android.
    """
    warnings.warn(
        "dbmail.providers.boxcar is deprecated: the Boxcar service has "
        "been end-of-life since ~2016. This provider will be removed "
        "in dbmail 4.0; migrate to APNs or FCM.",
        DeprecationWarning,
        stacklevel=2,
    )
    headers = {
        "Content-type": "application/x-www-form-urlencoded",
        "User-Agent": "DBMail/%s" % get_version(),
    }

    data = {"user_credentials": token, "notification[title]": from_unicode(title), "notification[sound]": "notifier-2"}

    api_url = kwargs.pop("api_url", "new.boxcar.io")
    for k, v in kwargs.items():
        data["notification[%s]" % k] = from_unicode(v)

    http = HTTPSConnection(api_url, timeout=10)
    try:
        http.request("POST", "/api/notifications", headers=headers, body=urlencode(data))
        response = http.getresponse()

        if response.status != 201:
            raise BoxcarError(response.reason)
    finally:
        http.close()
    return True
