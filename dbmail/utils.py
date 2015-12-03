# -*- encoding: utf-8 -*-

from django.utils.html import strip_tags

from dbmail import import_module


def premailer_transform(text):
    try:
        from premailer import transform

        return transform(text)
    except Exception as err:
        print(err)
        return text


def get_ip(request):
    try:
        from ipware.ip import get_real_ip

        ip = get_real_ip(request)
        if ip is not None:
            return ip.strip()
    except ImportError:
        pass

    return request.META['REMOTE_ADDR'].split(',')[-1].strip()


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
