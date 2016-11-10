# -*- coding: utf-8 -*-

try:
    from httplib import HTTPConnection
    from urllib import urlencode
except ImportError:
    from http.client import HTTPConnection
    from urllib.parse import urlencode


from django.conf import settings

from dbmail.providers.prowl.push import from_unicode
from dbmail import get_version

import json


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
        'text': from_unicode(sms_body),
        'answer': 'json',
    })

    http = HTTPConnection(kwargs.pop("api_url", "gate.smsaero.ru"))
    http.request("GET", "/send/?" + urlencode(kwargs), headers=headers)
    response = http.getresponse()

    if response.status != 200:
        raise AeroSmsError(response.reason)

    read = response.read().decode(response.headers.get_content_charset())
    data = json.loads(read)

    status = None
    if 'result' in data:
        status = data['result']

    sms_id = None
    if 'id' in data:
        sms_id = data['id']

    if sms_id and status == 'accepted':
        return True
    return False
