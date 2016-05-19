# -*- encoding: utf-8 -*-

import hmac
from hashlib import sha256
from json import dumps
from urllib import urlencode
from urllib2 import urlopen, Request

from django.conf import settings


class CentrifugoError(Exception):
    pass


def send(channel, data, **kwargs):
    if type(data) not in (set, dict, list, tuple):
        kwargs['message'] = data

    data = dumps([{
        "method": "publish",
        "params": {
            "channel": channel,
            "data": kwargs,
        },
    }])
    sign = hmac.new(settings.CENTRIFUGO_TOKEN, data, sha256).hexdigest()
    payload = urlencode({'data': data, 'sign': sign})

    response = urlopen(
        Request(settings.CENTRIFUGO_API),
        payload,
        timeout=10
    )
    if response.code != 200:
        raise CentrifugoError(response.read())
    return True
