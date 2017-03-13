# -*- coding: utf-8 -*-
from twilio.rest import TwilioRestClient

from django.conf import settings


class TwilioSmsError(Exception):
    pass


def send(sms_to, sms_body, **kwargs):
    """
    Site: https://www.twilio.com/
    API: https://www.twilio.com/docs/api/rest/sending-messages
    """

    params = {
        'from_': settings.TWILIO_FROM,
        'to': sms_to,
        'body': sms_body
    }

    client = TwilioRestClient(settings.TWILIO_ACCOUNT_SID,
                              settings.TWILIO_AUTH_TOKEN)

    response = client.messages.create(**params)

    return response.sid
