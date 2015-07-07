# -*- coding: utf-8 -*-

from httplib import HTTPConnection
from urllib import urlencode

from django.conf import settings

from dbmail.providers.prowl.push import from_unicode
from dbmail import get_version


class AeroSmsError(Exception):
    pass


def send(sms_to, sms_body, **kwargs):
    """
    Site: http://smsaero.ru/
    API: http://smsaero.ru/api/
    """
    headers = {
        "User-Agent": "DBMail/%s" % get_version(),
    }

    kwargs.update({
        'user': settings.SMSAERO_LOGIN,
        'password': settings.SMSAERO_MD5_PASSWORD,
        'from': kwargs.pop('sms_from', settings.SMSAERO_FROM),
        'to': sms_to.replace('+', ''),
        'text': from_unicode(sms_body)
    })

    http = HTTPConnection(kwargs.pop("api_url", "gate.smsaero.ru"))
    http.request("GET", "/send/?" + urlencode(kwargs), headers=headers)
    response = http.getresponse()

    if response.status != 200:
        raise AeroSmsError(response.reason)

    body = response.read().strip()
    if '=accepted' not in body:
        raise AeroSmsError(body)

    return int(body.split('=')[0])
