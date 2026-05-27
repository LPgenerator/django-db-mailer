from __future__ import annotations

import json
from http.client import HTTPSConnection
from urllib.parse import urlencode

from django.conf import settings

from dbmail import get_version
from dbmail.providers._compat import from_unicode


class AeroSmsError(Exception):
    pass


def send(sms_to, sms_body, **kwargs):
    """
    Site: https://smsaero.ru/
    API: https://smsaero.ru/api/
    """
    headers = {
        "User-Agent": "DBMail/%s" % get_version(),
    }

    kwargs.update(
        {
            "user": settings.SMSAERO_LOGIN,
            "password": settings.SMSAERO_MD5_PASSWORD,
            "from": kwargs.pop("sms_from", settings.SMSAERO_FROM),
            "to": sms_to.replace("+", ""),
            "text": from_unicode(sms_body),
            "answer": "json",
        }
    )

    http = HTTPSConnection(kwargs.pop("api_url", "gate.smsaero.ru"), timeout=10)
    try:
        http.request("GET", "/send/?" + urlencode(kwargs), headers=headers)
        response = http.getresponse()

        if response.status != 200:
            raise AeroSmsError(response.reason)

        read = response.read().decode(response.headers.get_content_charset() or "utf-8")
    finally:
        http.close()
    data = json.loads(read)

    status = None
    if "result" in data:
        status = data["result"]

    sms_id = None
    if "id" in data:
        sms_id = data["id"]

    if sms_id and status == "accepted":
        return True
    return False
