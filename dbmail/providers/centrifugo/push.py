from __future__ import annotations

import hmac
from hashlib import sha256
from json import dumps
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from django.conf import settings


class CentrifugoError(Exception):
    pass


def send(channel, data, **kwargs):
    if type(data) not in (set, dict, list, tuple):
        kwargs["message"] = data

    data = dumps(
        [
            {
                "method": "publish",
                "params": {
                    "channel": channel,
                    "data": kwargs,
                },
            }
        ]
    )
    secret = settings.CENTRIFUGO_TOKEN
    if isinstance(secret, str):
        secret = secret.encode("utf-8")
    sign = hmac.new(secret, data.encode("utf-8"), sha256).hexdigest()
    payload = urlencode({"data": data, "sign": sign}).encode("utf-8")

    response = urlopen(Request(settings.CENTRIFUGO_API), payload, timeout=10)
    if response.code != 200:
        raise CentrifugoError(response.read())
    return True
