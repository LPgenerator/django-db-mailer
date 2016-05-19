# -*- encoding: utf-8 -*-

from httplib import HTTPConnection, HTTPSConnection
from urlparse import urlparse
from json import dumps

from django.conf import settings


class HTTPError(Exception):
    pass


def send(hook_url, message, **kwargs):
    headers = {
        "Content-type": "application/json"
    }

    http_key = kwargs.pop("http_key", None)
    if not http_key and hasattr(settings, 'HTTP_KEY'):
        http_key = settings.HTTP_KEY
    headers["Authorization"] = "key={}".format(http_key)

    kwargs["msg"] = message

    up = urlparse(hook_url)
    if up.scheme == 'https':
        http = HTTPSConnection(up.netloc)
    else:
        http = HTTPConnection(up.netloc)

    http.request(
        "POST", up.path,
        headers=headers,
        body=dumps(kwargs))
    response = http.getresponse()

    if response.status != 200:
        raise HTTPError(response.reason)
    return True
