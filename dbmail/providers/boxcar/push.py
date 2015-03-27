# -*- encoding: utf-8 -*-

from httplib import HTTPSConnection
from urllib import urlencode

from dbmail.providers.prowl.push import from_unicode
from dbmail import get_version


class BoxcarError(Exception):
    pass


def send(token, title, **kwargs):
    """
    Site: https://boxcar.io/
    API: http://help.boxcar.io/knowledgebase/topics/48115-boxcar-api
    Desc: Best app for system administrators
    """
    headers = {
        "Content-type": "application/x-www-form-urlencoded",
        "User-Agent": "DBMail/%s" % get_version(),
    }

    data = {
        "user_credentials": token,
        "notification[title]": from_unicode(title),
        "notification[sound]": "notifier-2"
    }

    for k, v in kwargs.items():
        data['notification[%s]' % k] = from_unicode(v)

    http = HTTPSConnection(kwargs.pop("api_url", "new.boxcar.io"))
    http.request(
        "POST", "/api/notifications",
        headers=headers,
        body=urlencode(data))
    response = http.getresponse()

    if response.status != 201:
        raise BoxcarError(response.reason)
    return True
