# -*- coding: utf-8 -*-

from urllib import urlopen, urlencode
from json import loads

from django.conf import settings


class NexmoSmsError(Exception):
    pass


def send(sms_to, sms_body, **kwargs):
    try:
        text = sms_body.encode('utf-8', 'ignore')
    except UnicodeDecodeError:
        text = sms_body

    api_url = kwargs.pop('api_url', 'https://rest.nexmo.com/sms/json')
    params = {
        'api_key': settings.NEXMO_USERNAME,
        'api_secret': settings.NEXMO_PASSWORD,
        'from': kwargs.pop('sms_from', settings.NEXMO_FROM),
        'to': sms_to.replace('+', ''),
        'type': 'unicode',
        'lg': settings.NEXMO_LANG,
        'text': text
    }
    if kwargs:
        params.update(**kwargs)

    url = urlopen('%s?%s' % (api_url, urlencode(params)))
    messages = loads(url.read())

    response = messages.get('messages')
    if response and response[0].get('error-text'):
        raise NexmoSmsError(messages['messages'][0]['error-text'])
    elif 'status' in messages and messages.get('status') != '0':
        raise NexmoSmsError(messages.get('error-text'))
    return messages
