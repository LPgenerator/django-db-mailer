# -*- encoding: utf-8 -*-

from httplib import HTTPSConnection
from json import dumps, loads

from django.conf import settings

from dbmail import get_version


class ParseComError(Exception):
    pass


def send(device_id, description, **kwargs):
    """
    Site: http://parse.com
    API: https://www.parse.com/docs/push_guide#scheduled/REST
    Desc: Best app for system administrators
    """
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
        "data": {
            "alert": description,
            "title": kwargs.pop("event")
        }
    }

    _data = kwargs.pop('data', None)
    if _data is not None:
        data.update(_data)

    http = HTTPSConnection(kwargs.pop("api_url", "api.parse.com"))
    http.request(
        "POST", "/1/push",
        headers=headers,
        body=dumps(data))
    response = http.getresponse()

    if response.status != 200:
        raise ParseComError(response.reason)

    body = loads(response.read())
    if body['error']:
        raise ParseComError(body['error'])
    return True
