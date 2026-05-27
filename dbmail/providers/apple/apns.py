"""APNs binary protocol provider — DEPRECATED.

Apple shut down the binary APNs protocol on 2021-06. This provider
remains for installations that still target the legacy protocol over
the gateway.push.apple.com socket; it emits a ``DeprecationWarning``
on first use and will be removed in dbmail 4.0.

For modern installations use ``dbmail.providers.apple.apns2`` (HTTP/2
provider with JWT token auth).
"""

from __future__ import annotations

import ssl as _ssl
import warnings
from binascii import a2b_hex
from json import dumps
from socket import AF_INET, SOCK_STREAM, socket
from struct import pack
from time import time

from django.conf import settings

from dbmail import defaults
from dbmail.providers.apple.errors import APNsError


def send(token_hex, message, **kwargs):
    """
    Site: https://apple.com
    API: https://developer.apple.com
    Desc: iOS notifications via the LEGACY binary protocol.

    Note: Apple deprecated this protocol on 2021-06. Use
    ``dbmail.providers.apple.apns2`` for the supported HTTP/2 path.
    """
    warnings.warn(
        "dbmail.providers.apple.apns uses Apple's binary APNs protocol "
        "which was shut down on 2021-06. This provider will be removed "
        "in dbmail 4.0; use dbmail.providers.apple.apns2 instead.",
        DeprecationWarning,
        stacklevel=2,
    )

    is_enhanced = kwargs.pop("is_enhanced", False)
    identifier = kwargs.pop("identifier", 0)
    expiry = kwargs.pop("expiry", 0)

    alert = {
        "title": kwargs.pop("event"),
        "body": message,
        "action": kwargs.pop("apns_action", defaults.APNS_PROVIDER_DEFAULT_ACTION),
    }

    data = {"aps": {"alert": alert, "content-available": kwargs.pop("content_available", 0) and 1}}
    data["aps"].update(kwargs)
    payload_str = dumps(data, separators=(",", ":"))

    token = a2b_hex(token_hex)
    if is_enhanced is True:
        fmt = "!BIIH32sH%ds" % len(payload_str)
        expiry_at = int(time() + expiry) if expiry else 0
        notification = pack(fmt, 1, identifier, expiry_at, 32, token, len(payload_str), payload_str.encode("utf-8"))
    else:
        token_length_bin = pack(">H", len(token))
        payload_bytes = payload_str.encode("utf-8")
        plb = pack(">H", len(payload_bytes))
        notification = b"\0" + token_length_bin + token + plb + payload_bytes

    sock = socket(AF_INET, SOCK_STREAM)
    sock.settimeout(3)
    sock.connect((settings.APNS_GW_HOST, settings.APNS_GW_PORT))

    # Replaces the deprecated module-level ``ssl.wrap_socket`` (removed
    # in Python 3.12) with the modern context-based API.
    context = _ssl.create_default_context()
    context.load_cert_chain(certfile=settings.APNS_CERT_FILE, keyfile=settings.APNS_KEY_FILE)
    secure_sock = context.wrap_socket(sock, do_handshake_on_connect=False)

    result = secure_sock.write(notification)

    secure_sock.close()
    sock.close()

    if not result:
        raise APNsError

    return True
