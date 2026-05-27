from __future__ import annotations

from json import loads
from urllib.parse import urlencode
from urllib.request import Request, urlopen

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
        "type": kwargs.pop("req_type", "self"),
        "key": settings.PUSHALL_API_KEYS[ch]["key"],
        "id": settings.PUSHALL_API_KEYS[ch]["id"],
        "title": kwargs.pop("title", settings.PUSHALL_API_KEYS[ch].get("title") or ""),
        "text": message,
        "priority": kwargs.pop("priority", settings.PUSHALL_API_KEYS[ch].get("priority") or "0"),
    }
    if kwargs:
        params.update(**kwargs)

    payload = urlencode(params).encode("utf-8")
    with urlopen(Request("https://pushall.ru/api.php"), payload, timeout=10) as response:
        body = response.read()
        if response.status != 200:
            raise PushAllError(body)

    json = loads(body) if body else {}
    if json.get("error"):
        raise PushAllError(json.get("error"))

    return True
