# -*- encoding: utf-8 -*-

from pprint import pprint

from django.shortcuts import render

from dbmail import signals


def browser_notification(request):
    return render(request, "browser_noitification.html")


def web_push_notification(request):
    return render(request, "web-push.html")


def _dump_push_signals(**kwargs):
    kwargs.pop('instace', None)
    kwargs.pop('sender', None)
    kwargs.pop('signal', None)
    pprint(kwargs)


signals.safari_subscribe.connect(_dump_push_signals)
signals.safari_unsubscribe.connect(_dump_push_signals)
signals.safari_error_log.connect(_dump_push_signals)

signals.push_subscribe.connect(_dump_push_signals)
signals.push_unsubscribe.connect(_dump_push_signals)
