from __future__ import annotations

import logging
from importlib import import_module

from django.utils.html import strip_tags

logger = logging.getLogger(__name__)


def premailer_transform(text):
    try:
        from premailer import transform

        return transform(text)
    except ImportError:
        logger.error("You don't have module 'premailer' installed")
        return text
    except Exception as err:
        logger.error(err)
        return text


def get_ip(request):
    """Resolve client IP via ``django-ipware``.

    Falls back to the last token of ``REMOTE_ADDR`` if the header is
    malformed (defensive — ipware should already cover this).
    """
    from ipware import get_client_ip

    ip, _routable = get_client_ip(request)
    if ip:
        return ip
    return request.META.get("REMOTE_ADDR", "").split(",")[-1].strip() or None


def html2text(message):
    try:
        from html2text import html2text

        return html2text(message)
    except ImportError:
        return strip_tags(message)


def clean_html(message):
    from dbmail.defaults import MESSAGE_HTML2TEXT

    module = import_module(MESSAGE_HTML2TEXT)
    return module.html2text(message)
