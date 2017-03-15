# -*- encoding: utf-8 -*-

from json import dumps
from socket import socket
import struct
from binascii import unhexlify
import ssl
from contextlib import closing

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured

from dbmail import defaults


class APNSServerError(Exception):
    def __init__(self, status, identifier):
        super(APNSServerError, self).__init__(status, identifier)
        self.status = status
        self.identifier = identifier


def _apns_pack_frame(token_hex, payload, identifier, expiration, priority):
    token = unhexlify(token_hex)
    # |COMMAND|FRAME-LEN|{token}|{payload}|{id:4}|{expiration:4}|{priority:1}
    # 5 items, each 3 bytes prefix, then each item length
    frame_len = 3 * 5 + len(token) + len(payload) + 4 + 4 + 1
    frame_fmt = "!BIBH%ssBH%ssBHIBHIBHB" % (len(token), len(payload))
    frame = struct.pack(
        frame_fmt,
        2, frame_len,
        1, len(token), token,
        2, len(payload), payload,
        3, 4, identifier,
        4, 4, expiration,
        5, 1, priority
    )

    return frame


def _check_certificate(ss):
    mode = "start"
    for s in ss.split("\n"):
        if mode == "start":
            if "BEGIN RSA PRIVATE KEY" in s or "BEGIN PRIVATE KEY" in s:
                mode = "key"
        elif mode == "key":
            if "END RSA PRIVATE KEY" in s or "END PRIVATE KEY" in s:
                mode = "end"
                break
            elif s.startswith("Proc-Type") and "ENCRYPTED" in s:
                raise ImproperlyConfigured("Encrypted APNS private keys are not supported")

    if mode != "end":
        raise ImproperlyConfigured("The APNS certificate doesn't contain a private key")


def _apns_create_socket(address_tuple, certfile=None):
    certfile = certfile or settings.APNS_CERTIFICATE
    if not certfile:
        raise ImproperlyConfigured(
                'You need to set PUSH_NOTIFICATIONS_SETTINGS["APNS_CERTIFICATE"] to send APNS messages.'
                )

    try:
        with open(certfile, "r") as f:
            content = f.read()
    except Exception as e:
        msg = "The APNS certificate file at %r is not readable: %s" % (certfile, e)
        raise ImproperlyConfigured(msg)

    _check_certificate(content)

    sock = socket()
    sock = ssl.wrap_socket(
            sock, ssl_version=ssl.PROTOCOL_TLSv1, certfile=certfile, ca_certs=None
            )
    sock.connect(address_tuple)

    return sock


def _apns_check_errors(sock):
    timeout = None
    if timeout is None:
        return  # assume everything went fine!
    saved_timeout = sock.gettimeout()
    try:
        sock.settimeout(timeout)
        data = sock.recv(6)
        if data:
            command, status, identifier = struct.unpack("!BBI", data)
            # apple protocol says command is always 8. See http://goo.gl/ENUjXg
            assert command == 8, "Command must be 8!"
            if status != 0:
                raise APNSServerError(status, identifier)
    except socket.timeout:  # py3, see http://bugs.python.org/issue10272
        pass
    except ssl.SSLError as e:  # py2
        if "timed out" not in e.message:
            raise
    finally:
        sock.settimeout(saved_timeout)


def send(token, message, **kwargs):
    """
    Site: https://apple.com
    API: https://developer.apple.com
    Desc: iOS notifications
    """
    identifier = kwargs.pop('identifier', 0)
    expiry = kwargs.pop('expiry', 0)

    alert = {
        "title": kwargs.pop("event"),
        "body": message,
        "action": kwargs.pop(
            'apns_action', defaults.APNS_PROVIDER_DEFAULT_ACTION)
    }

    data = {
        "aps": {
            'alert': alert,
            'content-available': kwargs.pop('content_available', 0) and 1
        }
    }
    data['aps'].update(kwargs)
    payload = dumps(data, separators=(",", ":"), sort_keys=True).encode("utf-8")

    priority = 10

    frame = _apns_pack_frame(token, payload, identifier, expiry, priority)

    with closing(_apns_create_socket((settings.APNS_GW_HOST, settings.APNS_GW_PORT))) as socket:
        socket.write(frame)
        _apns_check_errors(socket)

    return True
