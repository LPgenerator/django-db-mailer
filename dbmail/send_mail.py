# -*- encoding: utf-8 -*-

import traceback
import pprint
import uuid
import time

from django.db.models.fields.related import ManyToManyField, ForeignKey
from django.core.mail import EmailMessage, EmailMultiAlternatives
from django.contrib.sites.models import Site
from django.template import Template, Context
from django.core.urlresolvers import reverse
from django.core.mail import get_connection
from django.utils.html import strip_tags
from django.utils import translation
from django.conf import settings
from django.core import signing

from dbmail.defaults import SHOW_CONTEXT, ENABLE_LOGGING, ADD_HEADER
from dbmail.models import MailTemplate, MailLog, MailGroup
from dbmail import get_version
from dbmail import defaults


class SendMail(object):
    def __init__(self, slug, recipient, *args, **kwargs):
        self._slug = slug

        self._recipient_list = self.__get_recipient_list(recipient)
        self._cc = self.__email_to_list(kwargs.pop('cc', None))
        self._bcc = self.__email_to_list(kwargs.pop('bcc', None))
        self._user = kwargs.pop('user', None)
        self._language = kwargs.pop('language', None)

        self._template = self.__get_template()
        self._context = self.__get_context(args)

        self._subject = self.__get_subject()
        self._message = self.__get_message()
        self._files = kwargs.pop('files', [])
        self._kwargs = kwargs
        self._num = 1
        self._err_msg = None
        self._err_exc = None
        self._log_id = self.__get_log_id()

        self._kwargs.pop('retry', None)
        self._kwargs.pop('max_retries', None)
        self._kwargs.pop('retry_delay', None)

        self._from_email = self.__get_from_email()
        self.__update_bcc_from_template_settings()
        self.__insert_mailer_identification_head()

    @staticmethod
    def __get_log_id():
        return '%f-%s' % (time.time(), uuid.uuid4())

    def __insert_mailer_identification_head(self):
        if not ADD_HEADER:
            return
        headers = self._kwargs.pop('headers', {})
        headers.update(
            {'X-Mailer-Wrapper': 'django-db-mailer ver %s' % get_version()})
        self._kwargs['headers'] = headers

    def __get_connection(self):
        if self._template.auth_credentials:
            return self._kwargs.pop('connection', None) or get_connection(
                **self._template.auth_credentials)
        return self._kwargs.pop('connection', None)

    def __get_template(self):
        return MailTemplate.get_template(slug=self._slug)

    def __get_context(self, context_list):
        try:
            data = self.__model_to_dict(Site.objects.get_current())
        except Site.DoesNotExist:
            data = {}

        for context in context_list:
            if isinstance(context, dict):
                data.update(context)
            elif hasattr(context, '_meta'):
                data.update(self.__model_to_dict(context))
                data.update({context._meta.module_name: context})

        if settings.DEBUG and SHOW_CONTEXT:
            pprint.pprint(data)
        return data

    def __get_str_by_language(self, field):
        template = getattr(self._template, field)
        if self._language is not None:
            field = '%s_%s' % (field, self._language)
            if hasattr(self._template, field):
                if getattr(self._template, field):
                    template = getattr(self._template, field)
        return template

    def __get_subject(self):
        return self.__render_template(
            self.__get_str_by_language('subject'), self._context)

    def __get_message(self):
        return self.__render_template(
            self.__get_str_by_language('message'), self._context)

    def __get_msg_with_track(self):
        message = self._message
        if ENABLE_LOGGING and self._template.enable_log:
            try:
                domain = Site.objects.get_current().domain
                encrypted = signing.dumps(self._log_id, compress=True)
                path = reverse('db-mail-tracker', args=[encrypted])
                message += defaults.TRACK_HTML % {
                    'url': 'http://%s%s' % (domain, path)}
            except Site.DoesNotExist:
                pass
        return message

    def __attach_files(self, mail):
        for file_object in self._template.files_list:
            mail.attach_file(file_object.filename.path)

        for filename in self._files:
            mail.attach_file(filename)

    def __send_html_message(self):
        msg = EmailMultiAlternatives(
            self._subject, strip_tags(self._message), cc=self._cc,
            from_email=self._from_email, to=self._recipient_list,
            bcc=self._bcc, connection=self.__get_connection(), **self._kwargs
        )
        msg.attach_alternative(self.__get_msg_with_track(), "text/html")
        self.__attach_files(msg)
        msg.send()

    def __send_plain_message(self):
        msg = EmailMessage(
            self._subject, self._message, from_email=self._from_email,
            to=self._recipient_list, cc=self._cc, bcc=self._bcc,
            connection=self.__get_connection(), **self._kwargs
        )
        self.__attach_files(msg)
        msg.send()

    def __get_recipient_list(self, recipient):
        if not isinstance(recipient, list) and '@' not in recipient:
            return self.__group_emails(recipient)
        return self.__email_to_list(recipient)

    def __update_bcc_from_template_settings(self):
        if self._template.bcc_list:
            if self._bcc:
                self._bcc.extend(self._template.bcc_list)
            else:
                self._bcc = self._template.bcc_list

    def __get_from_email(self):
        if self._kwargs.get('from_email'):
            return self._kwargs.pop('from_email', None)
        elif not self._template.from_email:
            return settings.DEFAULT_FROM_EMAIL
        return self._template.from_email.get_mail_from

    @staticmethod
    def __group_emails(recipient):
        email_list = []
        for slug in recipient.split(','):
            email_list.extend(MailGroup.get_emails(slug))
        return list(set(email_list))

    @staticmethod
    def __email_to_list(recipient):
        if recipient is None:
            return None
        elif not isinstance(recipient, list):
            recipient = [d.strip() for d in recipient.split(',') if d.strip()]
        return recipient

    def __render_template(self, template, context):
        translation.activate(self._language or settings.LANGUAGE_CODE)
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
        if ENABLE_LOGGING is True:
            if self._template.enable_log or not is_sent:
                MailLog.store(
                    self._recipient_list, self._cc, self._bcc,
                    is_sent, self._template, self._user,
                    self._num, self._err_msg, self._err_exc, self._log_id
                )

    def __try_to_send(self):
        for self._num in range(1, self._template.num_of_retries + 1):
            try:
                self.__send()
                break
            except Exception, msg:
                print '[dbmail]', msg.__unicode__()
                if self._template.num_of_retries == self._num:
                    raise
                time.sleep(defaults.SEND_RETRY_DELAY_DIRECT)

    def send(self, is_celery=True):
        if self._template.is_active:
            try:
                if is_celery is True:
                    self.__send()
                else:
                    self.__try_to_send()
                self.__store_log(True)
                return 'OK'
            except Exception as exc:
                self._err_msg = traceback.format_exc()
                self._err_exc = exc.__class__.__name__
                self.__store_log(False)
                raise
