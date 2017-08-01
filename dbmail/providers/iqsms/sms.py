# -*- encoding: utf-8 -*-

try:
    from httplib import HTTPConnection
    from urllib import urlencode
except ImportError:
    from http.client import HTTPConnection
    from urllib.parse import urlencode

from base64 import b64encode

from django.conf import settings

from dbmail.providers.prowl.push import from_unicode
from dbmail import get_version


class IQSMSError(Exception):
    pass


def send(sms_to, sms_body, **kwargs):
    """
    Site: http://iqsms.ru/
    API: http://iqsms.ru/api/
    """
    headers = {
        "User-Agent": "DBMail/%s" % get_version(),
        'Authorization': 'Basic %s' % b64encode(
            "%s:%s" % (
                settings.IQSMS_API_LOGIN, settings.IQSMS_API_PASSWORD
            )).decode("ascii")
    }

    kwargs.update({
        'phone': sms_to,
        'text': from_unicode(sms_body),
        'sender': kwargs.pop('sms_from', settings.IQSMS_FROM)
    })

    http = HTTPConnection(kwargs.pop("api_url", "gate.iqsms.ru"))
    http.request("GET", "/send/?" + urlencode(kwargs), headers=headers)
    response = http.getresponse()

    if response.status != 200:
        raise IQSMSError(response.reason)

    body = response.read().strip()
    if '=accepted' not in body:
        raise IQSMSError(body)

    return int(body.split('=')[0])
