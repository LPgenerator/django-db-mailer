# -*- coding: utf-8 -*-

from httplib import HTTPSConnection
from urllib import urlencode
from base64 import b64encode
from json import loads

from django.conf import settings

from dbmail.providers.prowl.push import from_unicode
from dbmail import get_version


class TwilioSmsError(Exception):
    pass


def send(sms_to, sms_body, **kwargs):
    """
    Site: https://www.twilio.com/
    API: https://www.twilio.com/docs/api/rest/sending-messages
    """
    headers = {
        "Content-type": "application/x-www-form-urlencoded",
        "User-Agent": "DBMail/%s" % get_version(),
        'Authorization': 'Basic %s' % b64encode(
            "%s:%s" % (
                settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN
            )).decode("ascii")

    }

    kwargs.update({
        'From': kwargs.pop('sms_from', settings.TWILIO_FROM),
        'To': sms_to,
        'Body': from_unicode(sms_body)
    })

    http = HTTPSConnection(kwargs.pop("api_url", "api.twilio.com"))
    http.request(
        "POST",
        "/2010-04-01/Accounts/%s/Messages.json" % settings.TWILIO_ACCOUNT_SID,
        headers=headers,
        body=urlencode(kwargs))

    response = http.getresponse()
    if response.status != 201:
        raise TwilioSmsError(response.reason)

    return loads(response.read()).get('sid')
