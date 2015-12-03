# -*- encoding: utf-8 -*-

import traceback
import pprint
import uuid
import time
import sys

from django.db.models.fields.related import ManyToManyField, ForeignKey
from django.core.mail import EmailMessage, EmailMultiAlternatives
from django.core.urlresolvers import reverse, NoReverseMatch
from django.contrib.sites.models import Site
from django.template import Template, Context
from django.core.mail import get_connection
from django.utils import translation
from django.conf import settings
from django.core import signing

from dbmail.defaults import SHOW_CONTEXT, ENABLE_LOGGING, ADD_HEADER
from dbmail.models import MailTemplate, MailLog, MailGroup
from dbmail.exceptions import StopSendingException
from dbmail.utils import clean_html
from dbmail import import_module
from dbmail import get_version
from dbmail import defaults


class Sender(object):
    def __init__(self, slug, recipient, *args, **kwargs):
        self._slug = slug

        self._recipient_list = self._get_recipient_list(recipient)
        self._cc = self._email_to_list(kwargs.pop('cc', None))
        self._bcc = self._email_to_list(kwargs.pop('bcc', None))
        self._user = kwargs.pop('user', None)
        self._language = kwargs.pop('language', None)
        self._backend = kwargs.pop('backend')
        self._provider = kwargs.pop('provider', None)
        self._signals_kw = kwargs.pop('signals_kwargs', {})

        self._template = self._get_template()
        self._context = self._get_context(args)

        self._subject = self._get_subject()
        self._message = self._get_message()
        self._files = kwargs.pop('files', [])
        self._kwargs = kwargs
        self._num = 1
        self._err_msg = None
        self._err_exc = None
        self._log_id = self._get_log_id()

        self._kwargs.pop('retry', None)
        self._kwargs.pop('max_retries', None)
        self._kwargs.pop('retry_delay', None)

        self._from_email = self._get_from_email()
        self._update_bcc_from_template_settings()
        self._insert_mailer_identification_head()

    @staticmethod
    def _get_log_id():
        return '%f-%s' % (time.time(), uuid.uuid4())

    def _insert_mailer_identification_head(self):
        if not ADD_HEADER:
            return
        headers = self._kwargs.pop('headers', {})
        headers.update(
            {'X-Mailer-Wrapper': 'django-db-mailer ver %s' % get_version()})
        self._kwargs['headers'] = headers

    def _get_connection(self):
        if self._template.auth_credentials:
            return self._kwargs.pop('connection', None) or get_connection(
                **self._template.auth_credentials)
        return self._kwargs.pop('connection', None)

    def _get_template(self):
        return MailTemplate.get_template(slug=self._slug)

    def _get_context(self, context_list):
        try:
            data = self._model_to_dict(Site.objects.get_current())
        except Site.DoesNotExist:
            data = {}

        for context in context_list:
            if isinstance(context, dict):
                data.update(context)
            elif hasattr(context, '_meta'):
                data.update(self._model_to_dict(context))
                data.update({self._get_context_module_name(context): context})

        if settings.DEBUG and SHOW_CONTEXT:
            pprint.pprint(data)
        return data

    @staticmethod
    def _get_context_module_name(context):
        from distutils.version import StrictVersion
        import django

        current_version = django.get_version()

        if StrictVersion(current_version) < StrictVersion('1.8'):
            return context._meta.module_name
        return context._meta.model_name

    def _get_str_by_language(self, field, template=None):
        obj = template if template else self._template
        template = getattr(obj, field)
        if self._language is not None:
            field = '%s_%s' % (field, self._language)
            if hasattr(obj, field):
                if getattr(obj, field):
                    template = getattr(obj, field)
        return template

    def _get_subject(self):
        return self._render_template(
            self._get_str_by_language('subject'), self._context)

    def _get_message_with_base(self):
        self._context['content'] = self._render_template(
            self._get_str_by_language('message'), self._context)
        return self._render_template(
            self._get_str_by_language('message', self._template.base),
            self._context
        )

    def _get_standard_message(self):
        return self._render_template(
            self._get_str_by_language('message'), self._context)

    def _get_message(self):
        if self._template.base:
            return self._get_message_with_base()
        return self._get_standard_message()

    def _get_msg_with_track(self):
        message = self._message
        if defaults.TRACK_ENABLE is False:
            return message
        if ENABLE_LOGGING and self._template.enable_log:
            try:
                domain = Site.objects.get_current().domain
                encrypted = signing.dumps(self._log_id, compress=True)
                path = reverse('db-mail-tracker', args=[encrypted])
                message += defaults.TRACK_HTML % {
                    'url': 'http://%s%s' % (domain, path)}
            except (Site.DoesNotExist, NoReverseMatch):
                pass
        return message

    def _attach_files(self, mail):
        for file_object in self._template.files_list:
            mail.attach_file(file_object.filename.path)

        for filename in self._files:
            mail.attach_file(filename)

    def _send_html_message(self):
        msg = EmailMultiAlternatives(
            self._subject, clean_html(self._message), cc=self._cc,
            from_email=self._from_email, to=self._recipient_list,
            bcc=self._bcc, connection=self._get_connection(), **self._kwargs
        )
        msg.attach_alternative(self._get_msg_with_track(), "text/html")
        self._attach_files(msg)
        msg.send()

    def _send_plain_message(self):
        msg = EmailMessage(
            self._subject, self._message, from_email=self._from_email,
            to=self._recipient_list, cc=self._cc, bcc=self._bcc,
            connection=self._get_connection(), **self._kwargs
        )
        self._attach_files(msg)
        msg.send()

    def _get_recipient_list(self, recipient):
        if not isinstance(recipient, list) and '@' not in recipient:
            return self._group_emails(recipient)
        return self._email_to_list(recipient)

    def _update_bcc_from_template_settings(self):
        if self._template.bcc_list:
            if self._bcc:
                self._bcc.extend(self._template.bcc_list)
            else:
                self._bcc = self._template.bcc_list

    def _get_from_email(self):
        if self._kwargs.get('from_email'):
            return self._kwargs.pop('from_email', None)
        elif not self._template.from_email:
            return settings.DEFAULT_FROM_EMAIL
        return self._template.from_email.get_mail_from

    @staticmethod
    def _group_emails(recipient):
        email_list = []
        for slug in recipient.split(','):
            email_list.extend(MailGroup.get_emails(slug))
        return list(set(email_list))

    @staticmethod
    def _email_to_list(recipient):
        if recipient is None:
            return None
        elif not isinstance(recipient, list):
            recipient = [d.strip() for d in recipient.split(',') if d.strip()]
        return recipient

    def _render_template(self, template, context):
        translation.activate(self._language or settings.LANGUAGE_CODE)
        return Template(template).render(Context(context))

    @staticmethod
    def _model_to_dict(instance):
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

    def _send_by_custom_provider(self):
        module = import_module(self._provider)
        module.send(self)

    def _send_by_native_provider(self):
        if self._template.is_html:
            return self._send_html_message()
        return self._send_plain_message()

    def _send(self):
        if self._provider is not None:
            return self._send_by_custom_provider()
        return self._send_by_native_provider()

    def _store_log(self, is_sent):
        if ENABLE_LOGGING is True:
            if self._template.enable_log or not is_sent:
                MailLog.store(
                    self._recipient_list, self._cc, self._bcc,
                    is_sent, self._template, self._user,
                    self._num, self._err_msg, self._err_exc,
                    self._log_id, self._backend, self._provider
                )

    def _try_to_send(self):
        for self._num in range(1, self._template.num_of_retries + 1):
            try:
                self._send()
                break
            except Exception as exc:
                print('[dbmail] %s' % exc)
                if self._template.num_of_retries == self._num:
                    raise
                time.sleep(defaults.SEND_RETRY_DELAY_DIRECT)

    def send(self, is_celery=True):
        from dbmail.signals import pre_send, post_send

        if self._template.is_active:
            try:
                pre_send.send(self.__class__, instace=self, **self._signals_kw)
                if is_celery is True:
                    self._send()
                else:
                    self._try_to_send()
                self._store_log(True)
                post_send.send(
                    self.__class__, instace=self, **self._signals_kw)
                return 'OK'
            except StopSendingException:
                return
            except Exception as exc:
                self._err_msg = traceback.format_exc()
                self._err_exc = exc.__class__.__name__
                self._store_log(False)
                raise

    @staticmethod
    def debug(key, value):
        from django.utils.termcolors import colorize

        if value:
            sys.stdout.write(colorize(key, fg='green'))
            sys.stdout.write(": ")
            sys.stdout.write(colorize(repr(value), fg='white'))
            sys.stdout.write("\n")


class SenderDebug(Sender):
    def _send(self):
        self.debug('Provider', self._provider or 'default')
        self.debug('Message', self._message)
        self.debug('From', self._from_email)
        self.debug('Recipients', self._recipient_list)
        self.debug('CC', self._cc)
        self.debug('BCC', self._bcc)
        self.debug('Additional kwargs', self._kwargs)
