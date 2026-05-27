"""Prowl push notifications.

Prowl is end-of-life as of ~2020; this provider is kept for backwards
compatibility and emits a ``DeprecationWarning`` on first use.

The ``from_unicode`` helper used to live here and is imported by eight
other providers. As of 3.0 it lives in
:mod:`dbmail.providers._compat`; the re-export below is kept for any
external code that imported it directly.
"""

from __future__ import annotations

import warnings
from http.client import HTTPSConnection
from urllib.parse import urlencode

from django.conf import settings

from dbmail import get_version
from dbmail.providers._compat import from_unicode as _from_unicode

__all__ = ("ProwlError", "from_unicode", "send")


class ProwlError(Exception):
    pass


def from_unicode(text, text_length=None):
    """Backwards-compatible re-export.

    Delegates to :func:`dbmail.providers._compat.from_unicode`. New
    code should import the helper from ``_compat`` directly.
    """
    warnings.warn(
        "dbmail.providers.prowl.push.from_unicode is moving — import from dbmail.providers._compat instead.",
        DeprecationWarning,
        stacklevel=2,
    )
    return _from_unicode(text, text_length)


def send(api_key, description, **kwargs):
    """
    Site: http://prowlapp.com
    API: http://prowlapp.com/api.php
    Desc: Best app for system administrators

    Note: Prowl service is end-of-life since ~2020. This provider remains
    for backwards compatibility; it will be removed in dbmail 4.0.
    """
    warnings.warn(
        "dbmail.providers.prowl is deprecated: the Prowl service is "
        "end-of-life since ~2020. Provider will be removed in 4.0; "
        "consider apns2 or pushover for iOS notifications.",
        DeprecationWarning,
        stacklevel=2,
    )

    headers = {
        "User-Agent": "DBMail/%s" % get_version(),
        "Content-type": "application/x-www-form-urlencoded",
    }

    application = _from_unicode(kwargs.pop("app", settings.PROWL_APP), 256)
    event = _from_unicode(kwargs.pop("event", "Alert"), 1024)
    description = _from_unicode(description, 10000)

    data = {
        "apikey": api_key,
        "application": application,
        "event": event,
        "description": description,
        "priority": kwargs.pop("priority", 1),
    }

    provider_key = kwargs.pop("providerkey", None)
    url = kwargs.pop("url", None)

    if provider_key is not None:
        data["providerkey"] = provider_key

    if url is not None:
        data["url"] = url[0:512]

    http = HTTPSConnection(kwargs.pop("api_url", "api.prowlapp.com"), timeout=10)
    try:
        http.request("POST", "/publicapi/add", headers=headers, body=urlencode(data))
        response = http.getresponse()

        if response.status != 200:
            raise ProwlError(response.reason)
    finally:
        http.close()
    return True
