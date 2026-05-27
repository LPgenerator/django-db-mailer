from __future__ import annotations

from http.client import HTTPSConnection
from json import dumps
from urllib.parse import urlencode, urlparse

from django.conf import settings

from dbmail import get_version
from dbmail.providers._compat import from_unicode


class SlackError(Exception):
    pass


def send(channel, message, **kwargs):
    """
    Site: https://slack.com
    API: https://api.slack.com
    Desc: real-time messaging
    """
    headers = {
        "Content-type": "application/x-www-form-urlencoded",
        "User-Agent": "DBMail/%s" % get_version(),
    }

    username = from_unicode(kwargs.pop("username", settings.SLACK_USERNAME))
    hook_url = from_unicode(kwargs.pop("hook_url", settings.SLACK_HOOCK_URL))
    channel = from_unicode(channel or settings.SLACK_CHANNEL)
    emoji = from_unicode(kwargs.pop("emoji", ""))
    message = from_unicode(message)

    data = {
        "channel": channel,
        "username": username,
        "text": message,
        "icon_emoji": emoji,
    }

    _data = kwargs.pop("data", None)
    if _data is not None:
        data.update(_data)

    up = urlparse(hook_url)
    http = HTTPSConnection(up.netloc, timeout=10)
    try:
        http.request("POST", up.path, headers=headers, body=urlencode({"payload": dumps(data)}))
        response = http.getresponse()

        if response.status != 200:
            raise SlackError(response.reason)

        body = response.read()
        if body != b"ok":
            raise SlackError(repr(body))
    finally:
        http.close()
    return True
