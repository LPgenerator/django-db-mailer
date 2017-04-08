# -*- encoding: utf-8 -*-

from http.client import HTTPSConnection
from json import dumps, loads
from urllib.parse import urlparse

from dbmail.defaults import GCM_KEY


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
        "Authorization": "key=" + kwargs.pop("gcm_key", GCM_KEY)
    }

    hook_url = 'https://android.googleapis.com/gcm/send'

    data = {
        "registration_ids": [user],
        "notification": {
            "title": kwargs.pop("event"),
            'body': message,
        },
        "data": {}
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
    if loads(body.decode('utf-8')).get("failure") > 0:
        raise GCMError(repr(body))
    return True
