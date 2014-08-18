# -*- encoding: utf-8 -*-

import json

from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import get_object_or_404
from django.http import HttpResponse, Http404
from django.core.cache import cache

from dbmail.models import ApiKey
from dbmail import send_db_mail

allowed_fields = [
    'api_key', 'slug', 'recipient', 'from_email', 'cc', 'bcc', 'queue',
    'retry_delay', 'max_retries', 'retry', 'time_limit', 'send_after',
]


@csrf_exempt
def send_by_dbmail(request):
    if request.method == 'POST':
        kwargs = dict()
        for f in allowed_fields:
            if request.POST.get(f):
                kwargs[f] = request.POST.get(f)

        api_key = kwargs.get('api_key')
        if api_key:
            del kwargs['api_key']
            if not cache.get(api_key):
                get_object_or_404(
                    ApiKey, api_key=api_key, is_active=True)
                cache.set(api_key, 1, timeout=None)

            args = []
            if request.POST.get('data'):
                args = [json.loads(request.POST['data'])]

            if kwargs.get('slug') and kwargs.get('recipient'):
                send_db_mail(
                    kwargs.pop('slug'), kwargs.pop('recipient'),
                    *args, **kwargs)
                return HttpResponse('OK')
    raise Http404
