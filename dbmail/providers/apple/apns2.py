from json import dumps

from django.conf import settings
from hyper import HTTP20Connection
from hyper.tls import init_context

from dbmail.providers.apple.errors import APNsError


def send(token_hex, message, **kwargs):
    """
    Site: https://apple.com
    API: https://developer.apple.com
    Desc: iOS notifications

    Installation and usage:
    pip install hyper
    """

    priority = kwargs.pop('priority', 10)
    topic = kwargs.pop('topic', None)
    data = {
        "aps": {
            'alert': message,
            'content-available': kwargs.pop('content_available', 0) and 1
        }
    }
    data['aps'].update(kwargs)
    payload = dumps(
        data, separators=(',', ':'), ensure_ascii=False).encode('utf-8')

    headers = {
        'apns-priority': priority
    }
    if topic is not None:
        headers['apns-topic'] = topic

    ssl_context = init_context()
    ssl_context.load_cert_chain(settings.APNS_CERT_FILE)
    connection = HTTP20Connection(
        settings.APNS_GW_HOST, settings.APNS_GW_PORT, ssl_context=ssl_context)

    stream_id = connection.request(
        'POST', '/3/device/{}'.format(token_hex), payload, headers)
    response = connection.get_response(stream_id)
    if response.status != 200:
        raise APNsError(response.read())
    return True
