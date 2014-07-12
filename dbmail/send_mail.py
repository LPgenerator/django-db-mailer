# -*- encoding: utf-8 -*-

import traceback
import time

from django.db.models.fields.related import ManyToManyField, ForeignKey
from django.core.mail import EmailMessage, EmailMultiAlternatives
from django.contrib.sites.models import Site
from django.template import Template, Context

from dbmail.models import MailTemplate, MailLog
from dbmail.defaults import RETRY_INTERVAL


class SendMail(object):
    def __init__(self, slug, recipient, *args, **kwargs):
        self._slug = slug

        self._recipient_list = self.__format_email_list(recipient)
        self._cc = self.__format_email_list(kwargs.pop('cc', None))
        self._bcc = self.__format_email_list(kwargs.pop('bcc', None))
        self._user = kwargs.pop('user', None)

        self._template = self.__get_template()
        self._context = self.__get_context(args)

        self._subject = self.__get_subject()
        self._message = self.__get_message()
        self._kwargs = kwargs
        self._num = 1
        self._err_msg = None

    def __get_template(self):
        return MailTemplate.get_template(slug=self._slug)

    def __get_context(self, context_list):
        data = self.__model_to_dict(Site.objects.get_current())
        for context in context_list:
            if isinstance(context, dict):
                data.update(context)
            else:
                data.update(self.__model_to_dict(context))
                data.update({context._meta.module_name: context})
        return data

    def __get_subject(self):
        return self.__render_template(self._template.subject, self._context)

    def __get_message(self):
        return self.__render_template(self._template.message, self._context)

    def __send_html_message(self):
        msg = EmailMultiAlternatives(
            self._subject, self._message, to=self._recipient_list,
            cc=self._cc, bcc=self._bcc, **self._kwargs)
        msg.attach_alternative(self._message, "text/html")
        msg.send()

    def __send_plain_message(self):
        msg = EmailMessage(
            self._subject, self._message, to=self._recipient_list,
            cc=self._cc, bcc=self._bcc, **self._kwargs)
        msg.send()

    @staticmethod
    def __format_email_list(recipient):
        if recipient is None:
            return None
        elif not isinstance(recipient, list):
            recipient = [d.strip() for d in recipient.split(',')]
        return recipient

    @staticmethod
    def __render_template(template, context):
        return Template(template).render(Context(context))

    @staticmethod
    def __model_to_dict(instance):
        opts, data = getattr(instance, '_meta'), dict()
        for f in opts.fields + opts.many_to_many:
            if isinstance(f, ManyToManyField):
                if instance.pk is None:
                    data[f.name] = []
                else:
                    data[f.name] = list(f.value_from_object(
                        instance).values_list('pk', flat=True))
            elif isinstance(f, ForeignKey):
                if getattr(instance, f.name):
                    data[f.name] = getattr(instance, f.name).__unicode__()
            else:
                data[f.name] = f.value_from_object(instance)
        return data

    def __send(self):
        if self._template.is_html:
            return self.__send_html_message()
        return self.__send_plain_message()

    def __store_log(self, is_sent):
        MailLog.store(
            self._recipient_list, self._cc, self._bcc,
            is_sent, self._template, self._user,
            self._num, self._err_msg
        )

    def __try_to_send(self):
        for self._num in range(1, self._template.num_of_retries + 1):
            try:
                self.__send()
            except Exception, msg:
                if self._template.num_of_retries == self._num:
                    self._err_msg = traceback.format_exc()
                    print '[dbmail]', msg.__unicode__()
                    raise
                time.sleep(RETRY_INTERVAL)

    def send(self):
        try:
            self.__try_to_send()
            self.__store_log(True)
        except Exception:
            self.__store_log(False)
            raise
