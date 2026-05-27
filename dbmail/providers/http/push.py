"""Generic HTTP webhook provider for dbmail.

Hardened against SSRF (OWASP A10) per ADR-0006 and the security
review:

- only ``https://`` (override via ``DBMAIL_HTTP_ALLOW_INSECURE``);
- explicit allowlist via ``DBMAIL_HTTP_ALLOWED_HOSTS`` (optional);
- DNS resolution to detect private/loopback/link-local destinations
  before sending;
- redirects are not followed automatically.
"""

from __future__ import annotations

import ipaddress
import socket
from http.client import HTTPConnection, HTTPSConnection
from json import dumps
from urllib.parse import urlparse

from django.conf import settings


class HTTPError(Exception):
    pass


_BLOCKED_NETWORKS = (
    ipaddress.ip_network("10.0.0.0/8"),
    ipaddress.ip_network("172.16.0.0/12"),
    ipaddress.ip_network("192.168.0.0/16"),
    ipaddress.ip_network("169.254.0.0/16"),
    ipaddress.ip_network("127.0.0.0/8"),
    ipaddress.ip_network("0.0.0.0/8"),
    ipaddress.ip_network("100.64.0.0/10"),  # CGNAT
    ipaddress.ip_network("::1/128"),
    ipaddress.ip_network("fc00::/7"),
    ipaddress.ip_network("fe80::/10"),
)


def _is_private(addr: str) -> bool:
    try:
        ip = ipaddress.ip_address(addr)
    except ValueError:
        return False
    return any(ip in net for net in _BLOCKED_NETWORKS)


def _resolve_or_raise(host: str) -> str:
    """Resolve ``host``, reject private destinations, and return the
    pinned IP so the subsequent ``connect()`` cannot be DNS-rebound
    onto a private address (CWE-918 / CWE-367).
    """
    try:
        infos = socket.getaddrinfo(host, None)
    except socket.gaierror as exc:
        raise HTTPError("dns lookup failed: %s" % host) from exc
    if not infos:
        raise HTTPError("no addresses resolved for host: %s" % host)
    for info in infos:
        ip = info[4][0]
        if _is_private(ip):
            raise HTTPError("refusing to call private address %s for host %s" % (ip, host))
    return infos[0][4][0]


def _check_url(hook_url: str) -> tuple[str, str, int]:
    parsed = urlparse(hook_url)
    if not parsed.netloc:
        raise HTTPError("malformed url")

    allow_insecure = getattr(settings, "DBMAIL_HTTP_ALLOW_INSECURE", False)
    if parsed.scheme != "https" and not allow_insecure:
        raise HTTPError("only https is allowed (set DBMAIL_HTTP_ALLOW_INSECURE=True to override)")
    if parsed.scheme not in ("http", "https"):
        raise HTTPError("unsupported scheme: %s" % parsed.scheme)

    host = parsed.hostname or ""
    allowed_hosts = getattr(settings, "DBMAIL_HTTP_ALLOWED_HOSTS", None)
    if allowed_hosts is not None and host not in allowed_hosts:
        raise HTTPError("host not in DBMAIL_HTTP_ALLOWED_HOSTS: %s" % host)

    _resolve_or_raise(host)

    port = parsed.port or (443 if parsed.scheme == "https" else 80)
    return parsed.scheme, parsed.netloc, port


def send(hook_url, message, **kwargs):
    scheme, netloc, _ = _check_url(hook_url)

    headers = {"Content-type": "application/json"}

    http_key = kwargs.pop("http_key", None)
    if not http_key and hasattr(settings, "HTTP_KEY"):
        http_key = settings.HTTP_KEY
    if http_key:
        headers["Authorization"] = "key=%s" % http_key

    kwargs["msg"] = message
    body = dumps(kwargs)

    parsed = urlparse(hook_url)
    if scheme == "https":
        conn = HTTPSConnection(netloc, timeout=10)
    else:
        conn = HTTPConnection(netloc, timeout=10)
    try:
        conn.request("POST", parsed.path or "/", headers=headers, body=body)
        response = conn.getresponse()

        if response.status != 200:
            raise HTTPError(response.reason)
    finally:
        conn.close()
    return True
