from __future__ import annotations

from json import loads
from urllib.parse import urlencode
from urllib.request import urlopen

from django.conf import settings

from dbmail.providers._compat import from_unicode


class NexmoSmsError(Exception):
    pass


def send(sms_to, sms_body, **kwargs):
    api_url = kwargs.pop("api_url", "https://rest.nexmo.com/sms/json")
    params = {
        "api_key": settings.NEXMO_USERNAME,
        "api_secret": settings.NEXMO_PASSWORD,
        "from": kwargs.pop("sms_from", settings.NEXMO_FROM),
        "to": str(sms_to).replace("+", ""),
        "type": "unicode",
        "lg": settings.NEXMO_LANG,
        "text": from_unicode(sms_body),
    }
    if kwargs:
        params.update(**kwargs)

    with urlopen("%s?%s" % (api_url, urlencode(params)), timeout=10) as url:
        messages = loads(url.read())

    response = messages.get("messages")
    if response and response[0].get("error-text"):
        raise NexmoSmsError(messages["messages"][0]["error-text"])
    elif "status" in messages and messages.get("status") != "0":
        raise NexmoSmsError(messages.get("error-text"))
    return messages
