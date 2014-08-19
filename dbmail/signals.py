# -*- encoding: utf-8 -*-

import datetime

from django.template import Template, Context
from django.contrib.sites.models import Site
from django.contrib.auth.models import User
from django.db.models import signals

from dbmail.defaults import SEND_RETRY, SEND_RETRY_DELAY
from dbmail.models import Signal, MailGroup
from dbmail.defaults import CELERY_QUEUE


class SignalReceiver(object):
    def __init__(self, sender, **kwargs):
        self.sender = sender
        self.kwargs = kwargs
        self.site = Site.objects.get_current()
        self.instance = kwargs.get('instance')
        self.pk = self.instance and self.instance.pk or None
        self.signal = None

        self.kwargs['old_instance'] = self.get_old_instance()
        self.kwargs['users'] = self.get_users()
        self.kwargs['date'] = datetime.date.today()
        self.kwargs['date_time'] = datetime.datetime.now()

        self.run()

    def get_signal_list(self):
        return Signal.objects.filter(
            model__model=self.sender._meta.module_name,
            is_active=True
        )

    def get_email_list(self):
        if self.signal.group:
            return MailGroup.get_emails(self.signal.group.slug)

        email_list = Template(self.signal.rules).render(Context(self.kwargs))
        return email_list.strip().replace('\r', '').replace('\n', '')

    def get_interval(self):
        options = dict()
        if self.signal.interval >= 0:
            options['send_after'] = self.signal.interval
        return options

    @staticmethod
    def get_users():
        return User.objects.filter(
            is_active=True, is_staff=False, is_superuser=False)

    def get_old_instance(self):
        instance = self.kwargs.get('instance')
        if instance and instance.pk:
            return self.sender.objects.get(
                pk=self.kwargs['instance'].pk)

    def send_mail(self):
        from dbmail import send_db_mail

        email_list = self.get_email_list()
        if email_list and not self.signal.is_sent(self.pk):
            send_db_mail(
                self.signal.template.slug, email_list, self.site,
                self.kwargs, self.instance, **self.get_interval()
            )
            self.signal.mark_as_sent(self.pk)

    def run(self):
        for self.signal in self.get_signal_list():
            self.send_mail()


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
            queue=CELERY_QUEUE,
        )
    else:
        SignalReceiver(sender, **kwargs)


def initial_signals():
    for signal in Signal.objects.filter(is_active=True):
        def_signal = getattr(signals, signal.signal)
        def_signal.connect(
            signal_receiver, sender=signal.model.model_class(),
            dispatch_uid=signal.model.name
        )
