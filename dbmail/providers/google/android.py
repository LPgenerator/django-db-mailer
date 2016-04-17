# -*- encoding: utf-8 -*-

from httplib import HTTPSConnection
from json import dumps, loads
from urlparse import urlparse

from django.conf import settings


class GCMError(Exception):
    pass


def send(user, message, **kwargs):
    """
    Site: https://developers.google.com
    API: https://developers.google.com/cloud-messaging/
    Desc: Android notifications
    """

    headers = {
        "Content-type": "application/json",
        "Authorization": "key=" + kwargs.pop("gcm_key", settings.GCM_KEY)
    }

    hook_url = 'https://android.googleapis.com/gcm/send'

    data = {
        "registration_ids": [user],
        "data": {
            "title": kwargs.pop("event"),
            'message': message,
        }
    }
    data['data'].update(kwargs)

    up = urlparse(hook_url)
    http = HTTPSConnection(up.netloc)
    http.request(
        "POST", up.path,
        headers=headers,
        body=dumps(data))
    response = http.getresponse()

    if response.status != 200:
        raise GCMError(response.reason)

    body = response.read()
    if loads(body).get("failure") > 0:
        raise GCMError(repr(body))
    return True
