# -*- encoding: utf-8 -*-

import json

from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import get_object_or_404
from django.http import HttpResponse, Http404
from django.core.cache import cache

from dbmail.models import ApiKey
from dbmail import db_sender
from dbmail import defaults


allowed_fields = [
    'api_key', 'slug', 'recipient', 'from_email', 'cc', 'bcc',
    'queue', 'retry_delay', 'max_retries', 'retry',
    'time_limit', 'send_after', 'backend', 'provider',
]


@csrf_exempt
def send_by_dbmail(request):
    if request.method == 'POST':
        kwargs = dict()
        for f in allowed_fields:
            if request.POST.get(f):
                kwargs[f] = request.POST.get(f)

        backend = defaults.BACKEND.get(kwargs.pop('backend', 'mail'))
        api_key = kwargs.get('api_key')
        if api_key:
            del kwargs['api_key']
            if not cache.get(api_key):
                get_object_or_404(
                    ApiKey, api_key=api_key, is_active=True)
                cache.set(api_key, 1, timeout=defaults.CACHE_TTL)

            args = []
            if request.POST.get('data'):
                args = [json.loads(request.POST['data'])]

            if kwargs.get('slug') and kwargs.get('recipient'):
                if backend is not None:
                    kwargs['backend'] = backend

                db_sender(
                    kwargs.pop('slug'), kwargs.pop('recipient'),
                    *args, **kwargs)
                return HttpResponse('OK')
    raise Http404


def mail_read_tracker(request, encrypted):
    if defaults.TRACK_ENABLE and defaults.ENABLE_LOGGING:
        from dbmail.tasks import mail_track

        req = {k: v for k, v in request.META.items()
               if k.startswith('HTTP_') or k.startswith('REMOTE')}
        if defaults.ENABLE_CELERY is True:
            mail_track.apply_async(args=[req, encrypted],
                                   retry=1, retry_policy={'max_retries': 3})
        else:
            mail_track(req, encrypted)

    return HttpResponse(
        content=defaults.TRACK_PIXEL[1],
        content_type=defaults.TRACK_PIXEL[0],
    )
