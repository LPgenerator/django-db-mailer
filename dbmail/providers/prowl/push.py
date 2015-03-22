# -*- encoding: utf-8 -*-

from httplib import HTTPSConnection
from urllib import urlencode

from django.conf import settings
from dbmail import get_version


class ProwlError(Exception):
    pass


def from_unicode(text, text_length=None):
    try:
        text = text.encode('utf-8', 'ignore')
    except UnicodeDecodeError:
        pass

    if text_length is not None:
        text = text[0:text_length]

    return text


def send(api_key, description, **kwargs):
    """
    Site: http://prowlapp.com
    API: http://prowlapp.com/api.php
    Desc: Best app for system administrators
    """
    headers = {
        "User-Agent": "DBMail/%s" % get_version(),
        "Content-type": "application/x-www-form-urlencoded"
    }

    application = from_unicode(kwargs.pop("app", settings.PROWL_APP), 256)
    event = from_unicode(kwargs.pop("event", 'Alert'), 1024)
    description = from_unicode(description, 10000)

    data = {
        "apikey": api_key,
        "application": application,
        "event": event,
        "description": description,
        "priority": kwargs.pop("priority", 1)
    }

    provider_key = kwargs.pop("providerkey", None)
    url = kwargs.pop('url', None)

    if provider_key is not None:
        data["providerkey"] = provider_key

    if url is not None:
        data["url"] = url[0:512]

    http = HTTPSConnection(kwargs.pop("api_url", "api.prowlapp.com"))
    http.request(
        "POST", "/publicapi/add",
        headers=headers,
        body=urlencode(data))
    response = http.getresponse()

    if response.status != 200:
        raise ProwlError(response.reason)
    return True
