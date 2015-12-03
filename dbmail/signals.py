# -*- encoding: utf-8 -*-

import datetime

from django.core.exceptions import ObjectDoesNotExist
from django.template import Template, Context
from django.contrib.sites.models import Site
from django.contrib.auth.models import User
from django.db.models import signals
from django import dispatch

from dbmail.defaults import (
    SIGNALS_QUEUE, SIGNALS_MAIL_QUEUE, SIGNAL_DEFERRED_DISPATCHER,
    ENABLE_USERS, SEND_RETRY, SEND_RETRY_DELAY
)
from dbmail.models import Signal, SignalDeferredDispatch


class SignalReceiver(object):
    def __init__(self, sender, **kwargs):
        self.sender = sender
        self.kwargs = kwargs
        self._kwargs = kwargs.copy()
        self.site = Site.objects.get_current()
        self.instance = kwargs.get('instance')
        self.pk = self.instance and self.instance.pk or None

        self.signal = None
        self.signal_pk = self.kwargs.pop('signal_pk', None)

        self.kwargs['old_instance'] = self.get_old_instance()
        self.kwargs['users'] = self.get_users()
        self.kwargs['date'] = datetime.date.today()
        self.kwargs['date_time'] = datetime.datetime.now()

    def get_signal_list(self):
        if not hasattr(self.sender._meta, 'module_name'):
            return Signal.objects.filter(
                model__model=self.sender._meta.model_name,
                is_active=True
            )
        return Signal.objects.filter(
            model__model=self.sender._meta.module_name,
            is_active=True
        )

    def get_email_list(self):
        if self.signal.group:
            return self.signal.group.slug

        email_list = Template(self.signal.rules).render(Context(self.kwargs))
        self.kwargs.pop('users', None)
        return email_list.strip().replace('\r', '').replace('\n', '')

    def get_interval(self):
        options = dict()
        if self.signal.interval >= 0 and not self.signal_pk:
            options['send_after'] = self.signal.interval
        return options

    @staticmethod
    def get_users():
        if ENABLE_USERS:
            return User.objects.filter(
                is_active=True, is_staff=False, is_superuser=False)
        return []

    def get_old_instance(self):
        try:
            instance = self.kwargs.get('instance')
            if instance and instance.pk:
                return self.sender.objects.get(
                    pk=self.kwargs['instance'].pk)
        except ObjectDoesNotExist:
            pass

    def get_current_instance(self):
        try:
            if self.instance and self.instance.pk and self.signal.update_model:
                obj = self.instance._default_manager.get(pk=self.instance.pk)
                self.kwargs['current_instance'] = obj
        except ObjectDoesNotExist:
            pass

    def send_mail(self):
        from dbmail import send_db_mail

        email_list = self.get_email_list()
        if email_list and not self.signal.is_sent(self.pk):
            for email in email_list.split(","):
                email = email.strip()
                if email:
                    send_db_mail(
                        self.signal.template.slug, email, self.site,
                        self.kwargs, self.instance, queue=SIGNALS_MAIL_QUEUE,
                        **self.get_interval()
                    )
            self.signal.mark_as_sent(self.pk)

    def _dispatch_deferred_task(self):
        self._kwargs['signal_pk'] = self.signal.pk

        if SIGNAL_DEFERRED_DISPATCHER == 'celery':
            from dbmail import tasks

            tasks.deferred_signal.apply_async(
                args=[self.sender], kwargs=self._kwargs,
                default_retry_delay=SEND_RETRY_DELAY,
                max_retries=SEND_RETRY,
                queue=SIGNALS_QUEUE,
                countdown=self.signal.interval
            )
        else:
            SignalDeferredDispatch.add_task(
                args=[self.sender], kwargs=self._kwargs,
                params=dict(
                    default_retry_delay=SEND_RETRY_DELAY,
                    max_retries=SEND_RETRY,
                    queue=SIGNALS_QUEUE
                ), interval=self.signal.interval
            )

    def _run(self):
        if self.signal.interval:
            self._dispatch_deferred_task()
        else:
            self.send_mail()

    def run(self):
        for self.signal in self.get_signal_list():
            self._run()

    def run_deferred(self):
        try:
            self.signal = Signal.objects.get(pk=self.signal_pk, is_active=True)
            self.get_current_instance()
            self.send_mail()
        except ObjectDoesNotExist:
            pass


def signal_receiver(sender, **kwargs):
    from dbmail import celery_supported

    if 'signal' in kwargs:
        kwargs.pop('signal')

    if celery_supported():
        import tasks

        tasks.signal_receiver.apply_async(
            args=[sender], kwargs=kwargs,
            default_retry_delay=SEND_RETRY_DELAY,
            max_retries=SEND_RETRY,
            queue=SIGNALS_QUEUE,
        )
    else:
        SignalReceiver(sender, **kwargs).run()


def initial_signals():
    for signal in Signal.objects.filter(is_active=True):
        def_signal = getattr(signals, signal.signal)
        def_signal.connect(
            signal_receiver, sender=signal.model.model_class(),
            dispatch_uid=signal.model.name
        )


pre_send = dispatch.Signal()
post_send = dispatch.Signal()
