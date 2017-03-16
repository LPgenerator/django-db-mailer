# -*- encoding: utf-8 -*-

from json import dumps
from socket import socket
import struct
import codecs
from binascii import unhexlify
import ssl
from contextlib import closing

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
    from dbmail.defaults import APNS_CERTIFICATE
    certfile = certfile or APNS_CERTIFICATE
    if not certfile:
        raise ImproperlyConfigured(
                'You need to set DB_APNS_CERTIFICATE to send APNS messages.'
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

    from dbmail.defaults import APNS_GW_PORT, APNS_GW_HOST
    with closing(_apns_create_socket((APNS_GW_HOST, APNS_GW_PORT))) as socket:
        socket.write(frame)
        _apns_check_errors(socket)

    return True


def _apns_read_and_unpack(socket, data_format):
    length = struct.calcsize(data_format)
    data = socket.recv(length)
    if data:
        return struct.unpack_from(data_format, data, 0)
    else:
        return None


def _apns_receive_feedback(socket):
    expired_token_list = []

    # read a timestamp (4 bytes) and device token length (2 bytes)
    header_format = "!LH"
    has_data = True
    while has_data:
        try:
            # read the header tuple
            header_data = _apns_read_and_unpack(socket, header_format)
            if header_data is not None:
                timestamp, token_length = header_data
                # Unpack format for a single value of length bytes
                token_format = "%ss" % token_length
                device_token = _apns_read_and_unpack(socket, token_format)
                if device_token is not None:
                    # _apns_read_and_unpack returns a tuple, but
                    # it's just one item, so get the first.
                    expired_token_list.append((timestamp, device_token[0]))
            else:
                has_data = False
        except socket.timeout:  # py3, see http://bugs.python.org/issue10272
            pass
        except ssl.SSLError as e:  # py2
            if "timed out" not in e.message:
                raise

    return expired_token_list


def apns_fetch_inactive_ids(certfile=None):
    """
    Queries the APNS server for id's that are no longer active since
    the last fetch
    """
    from dbmail.defaults import APNS_GW_PORT, APNS_GW_HOST
    with closing(_apns_create_socket((APNS_GW_HOST, APNS_GW_PORT))) as socket:
        inactive_ids = []
        # Maybe we should have a flag to return the timestamp?
        # It doesn't seem that useful right now, though.
        for ts, registration_id in _apns_receive_feedback(socket):
            inactive_ids.append(codecs.encode(registration_id, "hex_codec"))
        return inactive_ids
