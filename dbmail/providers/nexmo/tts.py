from __future__ import annotations


def send(tts_to, tts_body, **kwargs):
    from .sms import send

    kwargs["api_url"] = "https://api.nexmo.com/tts/json"
    return send(tts_to, tts_body, **kwargs)
