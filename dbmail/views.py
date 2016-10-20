# -*- encoding: utf-8 -*-

import json
import sys
import os

from django.http import HttpResponse, Http404, HttpResponseBadRequest
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.shortcuts import get_object_or_404
from django.views.generic import View
from django.core.cache import cache

from dbmail.models import ApiKey
from dbmail import db_sender
from dbmail import defaults

from dbmail import signals


allowed_fields = [
    'api_key', 'slug', 'recipient', 'from_email', 'cc', 'bcc',
    'queue', 'retry_delay', 'max_retries', 'retry', 'language',
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
            mail_track.apply_async(
                args=[req, encrypted], queue=defaults.TRACKING_QUEUE,
                retry=1, retry_policy={'max_retries': 3})
        else:
            mail_track(req, encrypted)

    return HttpResponse(
        content=defaults.TRACK_PIXEL[1],
        content_type=defaults.TRACK_PIXEL[0],
    )


class PostCSRFMixin(View):
    @method_decorator(csrf_exempt)
    def dispatch(self, request, *args, **kwargs):
        return super(PostCSRFMixin, self).dispatch(request, *args, **kwargs)


class SafariPushPackagesView(PostCSRFMixin):
    def post(self, _, version, site_pid):
        signals.safari_push_package.send(
            self.__class__, instance=self, version=version, site_pid=site_pid)

        pp = os.path.join(defaults.SAFARI_PUSH_PATH, '%s.zip' % site_pid)
        return HttpResponse(open(pp).read(), content_type='application/zip')


class SafariSubscriptionView(PostCSRFMixin):
    http_method_names = ['post', 'delete']

    def post(self, _, **kwargs):
        signals.safari_subscribe.send(self.__class__, instance=self, **kwargs)
        return HttpResponse()

    def delete(self, _, **kwargs):
        signals.safari_unsubscribe.send(
            self.__class__, instance=self, **kwargs)
        return HttpResponse()


class SafariLogView(PostCSRFMixin):
    def post(self, request, version):
        err = json.loads(request.body)
        signals.safari_error_log.send(self.__class__, instance=self, err=err)
        return HttpResponse()


class PushSubscriptionView(View):
    http_method_names = ['post', 'delete']

    def _process(self, request, signal, **kwargs):
        try:
            kwargs.update(json.loads(request.body))
            signal.send(self.__class__, instance=self, **kwargs)
            return HttpResponse()
        except ValueError:
            return HttpResponseBadRequest()

    def post(self, request, **kwargs):
        return self._process(request, signals.push_subscribe, **kwargs)

    def delete(self, request, **kwargs):
        return self._process(request, signals.push_unsubscribe, **kwargs)
