"""APNs HTTP/2 provider.

Replaces the legacy ``hyper``-based implementation (the ``hyper``
package has been unmaintained since 2020 and does not install on
Python 3.11+). Uses ``httpx`` with ``http2=True`` instead.

Authentication uses an APNs certificate (``settings.APNS_CERT_FILE``
plus an optional key file ``settings.APNS_KEY_FILE``). Token-based
JWT auth (``.p8`` file) is recommended by Apple but is intentionally
left for a separate provider variant in 3.x.

Optional dependency: ``pip install "django-db-mailer[apns]"`` installs
``httpx[http2]`` and ``pyjwt[crypto]``.
"""

from __future__ import annotations

from json import dumps

from django.conf import settings

from dbmail import defaults
from dbmail.providers.apple.errors import APNsError


def send(token_hex, message, **kwargs):
    """
    Site: https://apple.com
    API: https://developer.apple.com
    Desc: iOS notifications via APNs HTTP/2.

    Installation:
        pip install "django-db-mailer[apns]"
    """
    # Lazy import — keeps the provider module importable without httpx
    # so `python -c "import dbmail.providers.apple.apns2"` does not
    # require the optional extra to be installed.
    import httpx

    priority = kwargs.pop("priority", 10)
    topic = kwargs.pop("topic", None)

    alert = {
        "title": kwargs.pop("event"),
        "body": message,
        "action": kwargs.pop("apns_action", defaults.APNS_PROVIDER_DEFAULT_ACTION),
    }

    data = {"aps": {"alert": alert, "content-available": kwargs.pop("content_available", 0) and 1}}
    data["aps"].update(kwargs)
    payload = dumps(data, separators=(",", ":"))

    headers = {"apns-priority": str(priority)}
    if topic is not None:
        headers["apns-topic"] = topic

    cert = settings.APNS_CERT_FILE
    key_file = getattr(settings, "APNS_KEY_FILE", None)
    if key_file:
        cert = (settings.APNS_CERT_FILE, key_file)

    base_url = "https://%s:%d" % (settings.APNS_GW_HOST, settings.APNS_GW_PORT)
    timeout = httpx.Timeout(10.0, connect=5.0)

    with httpx.Client(http2=True, base_url=base_url, cert=cert, timeout=timeout) as client:
        response = client.post(
            "/3/device/%s" % token_hex,
            content=payload,
            headers=headers,
        )

    if response.status_code != 200:
        raise APNsError(response.text)
    return True
