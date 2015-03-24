# -*- encoding: utf-8 -*-

from httplib import HTTPSConnection
from urllib import urlencode
from json import loads

from django.conf import settings

from dbmail import get_version
from dbmail.providers.prowl.push import from_unicode


class PushOverError(Exception):
    pass


def send(user, message, **kwargs):
    """
    Site: https://pushover.net/
    API: https://pushover.net/api
    Desc: real-time notifications
    """
    headers = {
        "Content-type": "application/x-www-form-urlencoded",
        "User-Agent": "DBMail/%s" % get_version(),
    }

    title = from_unicode(kwargs.pop("title", settings.PUSHOVER_APP))
    message = from_unicode(message)

    data = {
        "token": settings.PUSHOVER_TOKEN,
        "user": user,
        "message": message,
        "title": title,
        "priority": kwargs.pop("priority", 0)
    }

    _data = kwargs.pop('data', None)
    if _data is not None:
        data.update(_data)

    http = HTTPSConnection(kwargs.pop("api_url", "api.pushover.net"))
    http.request(
        "POST", "/1/messages.json",
        headers=headers,
        body=urlencode(data))
    response = http.getresponse()

    if response.status != 200:
        raise PushOverError(response.reason)

    body = loads(response.read())
    if body.get('status') != 1:
        raise PushOverError(repr(body))
    return True
