from __future__ import annotations

import warnings

from django.conf import settings


class PubNubError(Exception):
    pass


def send(channel, message, **kwargs):
    """
    Site: https://www.pubnub.com/
    API: https://www.pubnub.com/docs/sdks/python
    Desc: real-time browser notifications.

    Requires ``pubnub>=7``. Install via the ``[pubnub]`` extra:
    ``pip install "django-db-mailer[pubnub]"``. The legacy capital-P
    ``Pubnub`` SDK (last release 2018) is no longer supported.
    """
    try:
        from pubnub.pnconfiguration import PNConfiguration
        from pubnub.pubnub import PubNub
    except ImportError as exc:  # pragma: no cover - opt-in extra
        raise PubNubError(
            "pubnub>=7 is required for the PubNub provider. Install via 'pip install \"django-db-mailer[pubnub]\"'."
        ) from exc

    pnconfig = PNConfiguration()
    pnconfig.publish_key = settings.PUBNUB_PUB_KEY
    pnconfig.subscribe_key = settings.PUBNUB_SUB_KEY
    pnconfig.secret_key = getattr(settings, "PUBNUB_SEC_KEY", None)
    pnconfig.ssl = bool(kwargs.pop("ssl_on", True))
    user_id = kwargs.pop("uuid", None) or getattr(settings, "PUBNUB_UUID", "django-db-mailer")
    pnconfig.uuid = user_id

    pubnub = PubNub(pnconfig)
    envelope = pubnub.publish().channel(channel).message({"text": message}).sync()
    if envelope.status.is_error():
        warnings.warn(repr(envelope.status), stacklevel=2)
        raise PubNubError(envelope.status.error_data.information)
    return True
