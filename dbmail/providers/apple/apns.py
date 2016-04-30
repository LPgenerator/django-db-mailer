# -*- encoding: utf-8 -*-

from binascii import a2b_hex
from json import dumps
from socket import socket, AF_INET, SOCK_STREAM
from struct import pack
from time import time

try:
    from ssl import wrap_socket
except ImportError:
    from socket import ssl as wrap_socket

from django.conf import settings

from dbmail.providers.apple.errors import APNsError
from dbmail import PY3


def send(token_hex, message, **kwargs):
    """
    Site: https://apple.com
    API: https://developer.apple.com
    Desc: iOS notifications
    """
    is_enhanced = kwargs.pop('is_enhanced', False)
    identifier = kwargs.pop('identifier', 0)
    expiry = kwargs.pop('expiry', 0)
    data = {
        "aps": {
            'alert': message,
            'content-available': kwargs.pop('content_available', 0) and 1
        }
    }
    data['aps'].update(kwargs)
    payload = dumps(
        data, separators=(',', ':'), ensure_ascii=False).encode('utf-8')

    token = a2b_hex(token_hex)
    if is_enhanced is True:
        fmt = '!BIIH32sH%ds' % len(payload)
        expiry = expiry and time() + expiry
        notification = pack(
            fmt, 1, identifier, expiry,
            32, token, len(payload), payload)
    else:
        token_length_bin = pack('>H', len(token))
        payload_length_bin = pack('>H', len(payload))
        zero_byte = bytes('\0', 'utf-8') if PY3 is True else '\0'
        notification = (
            zero_byte + token_length_bin + token +
            payload_length_bin + payload)

    sock = socket(AF_INET, SOCK_STREAM)
    sock.settimeout(3)
    sock.connect((settings.APNS_GW_HOST, settings.APNS_GW_PORT))
    ssl = wrap_socket(
        sock, settings.APNS_KEY_FILE,
        settings.APNS_CERT_FILE,
        do_handshake_on_connect=False)

    result = ssl.write(notification)

    sock.close()
    ssl.close()

    if not result:
        raise APNsError

    return True
