# -*- encoding: utf-8 -*-

from json import loads
from urllib import urlencode
from urllib2 import urlopen, Request

from django.conf import settings


class PushAllError(Exception):
    pass


def send(ch, message, **kwargs):
    """
    Site: https://pushall.ru
    API: https://pushall.ru/blog/api
    Desc: App for notification to devices/browsers and messaging apps
    """
    params = {
        'type': kwargs.pop('req_type', 'self'),
        'key': settings.PUSHALL_API_KEYS[ch]['key'],
        'id': settings.PUSHALL_API_KEYS[ch]['id'],
        'title': kwargs.pop(
            "title", settings.PUSHALL_API_KEYS[ch].get('title') or ""),
        'text': message,
        'priority': kwargs.pop(
            "priority", settings.PUSHALL_API_KEYS[ch].get('priority') or "0"),
    }
    if kwargs:
        params.update(**kwargs)

    response = urlopen(
        Request('https://pushall.ru/api.php'),
        urlencode(params),
        timeout=10
    )

    if response.code != 200:
        raise PushAllError(response.read())

    json = loads(response.read())
    if json.get('error'):
        raise PushAllError(json.get('error'))

    return True
