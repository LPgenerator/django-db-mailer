# -*- encoding: utf-8 -*-

import datetime
import pickle
import uuid
import os
import re

from django.utils.translation import ugettext_lazy as _
from django.utils.html import strip_tags
from django.utils.timezone import now
from django.core.cache import cache
from django.utils import timezone
from django.conf import settings
from django.db import models
from django import VERSION

from dbmail.defaults import (
    PRIORITY_STEPS, UPLOAD_TO, DEFAULT_CATEGORY, AUTH_USER_MODEL,
    DEFAULT_FROM_EMAIL, DEFAULT_PRIORITY, CACHE_TTL,
    BACKEND, _BACKEND, BACKENDS_MODEL_CHOICES, MODEL_HTMLFIELD)

from dbmail import initial_signals, import_by_string
from dbmail import python_2_unicode_compatible
from dbmail.utils import premailer_transform


HTMLField = import_by_string(MODEL_HTMLFIELD)


def _upload_mail_file(instance, filename):
    if instance is not None:
        ext = filename.split('.')[-1]
        filename = "%s.%s" % (str(uuid.uuid4()), ext)
        return os.path.join(UPLOAD_TO, filename)


@python_2_unicode_compatible
class MailCategory(models.Model):
    name = models.CharField(_('Category'), max_length=25, unique=True)
    created = models.DateTimeField(_('Created'), auto_now_add=True)
    updated = models.DateTimeField(_('Updated'), auto_now=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = _('Mail category')
        verbose_name_plural = _('Mail categories')


@python_2_unicode_compatible
class MailBaseTemplate(models.Model):
    name = models.CharField(_('Name'), max_length=100, unique=True)
    message = HTMLField(
        _('Body'), help_text=_(
            'Basic template for mail messages. {{content}} tag for msg.'))
    created = models.DateTimeField(_('Created'), auto_now_add=True)
    updated = models.DateTimeField(_('Updated'), auto_now=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = _('Mail base template')
        verbose_name_plural = _('Mail base templates')


@python_2_unicode_compatible
class MailFromEmailCredential(models.Model):
    host = models.CharField(_('Host'), max_length=50)
    port = models.PositiveIntegerField(_('Port'))
    username = models.CharField(
        _('Username'), max_length=50, null=True, blank=True)
    password = models.CharField(
        _('Password'), max_length=50, null=True, blank=True)
    use_tls = models.BooleanField(_('Use TLS'), default=False)
    fail_silently = models.BooleanField(_('Fail silently'), default=False)
    created = models.DateTimeField(_('Created'), auto_now_add=True)
    updated = models.DateTimeField(_('Updated'), auto_now=True)

    def _clean_cache(self):
        for obj in MailFromEmail.objects.filter(credential=self):
            obj._clean_template_cache()

    def delete(self, using=None):
        self._clean_cache()
        super(MailFromEmailCredential, self).delete(using)

    def save(self, *args, **kwargs):
        super(MailFromEmailCredential, self).save(*args, **kwargs)
        self._clean_cache()

    def __str__(self):
        return '%s/%s' % (self.username, self.host)

    class Meta:
        verbose_name = _('Mail auth settings')
        verbose_name_plural = _('Mail auth settings')


@python_2_unicode_compatible
class MailFromEmail(models.Model):
    name = models.CharField(_('Name'), max_length=100)
    email = models.CharField(
        _('Email'), max_length=75, unique=True,
        help_text=_('For sms/tts/push you must specify name or number'))
    credential = models.ForeignKey(
        MailFromEmailCredential, verbose_name=_('Auth credentials'),
        blank=True, null=True, default=None)
    created = models.DateTimeField(_('Created'), auto_now_add=True)
    updated = models.DateTimeField(_('Updated'), auto_now=True)

    @property
    def get_mail_from(self):
        return u'%s <%s>' % (self.name, self.email)

    def _clean_template_cache(self):
        MailTemplate.clean_cache(from_email=self)

    def get_auth(self):
        if self.credential:
            return dict(
                host=self.credential.host,
                port=self.credential.port,
                username=str(self.credential.username),
                password=str(self.credential.password),
                use_tls=self.credential.use_tls,
                fail_silently=self.credential.fail_silently
            )

    def delete(self, using=None):
        self._clean_template_cache()
        super(MailFromEmail, self).delete(using)

    def save(self, *args, **kwargs):
        super(MailFromEmail, self).save(*args, **kwargs)
        self._clean_template_cache()

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = _('Mail from')
        verbose_name_plural = _('Mail from')


@python_2_unicode_compatible
class MailBcc(models.Model):
    email = models.EmailField(_('Email'), unique=True)
    is_active = models.BooleanField(_('Is active'), default=True)
    created = models.DateTimeField(_('Created'), auto_now_add=True)
    updated = models.DateTimeField(_('Updated'), auto_now=True)

    def __clean_cache(self):
        MailTemplate.clean_cache(bcc_email=self)

    def save(self, *args, **kwargs):
        super(MailBcc, self).save(*args, **kwargs)
        self.__clean_cache()

    def delete(self, using=None):
        self.__clean_cache()
        super(MailBcc, self).delete(using)

    def __str__(self):
        return self.email

    class Meta:
        verbose_name = _('Mail Bcc')
        verbose_name_plural = _('Mail Bcc')


@python_2_unicode_compatible
class MailTemplate(models.Model):
    name = models.CharField(_('Template name'), max_length=100, db_index=True)
    subject = models.CharField(_('Subject'), max_length=100)
    from_email = models.ForeignKey(
        MailFromEmail, null=True, blank=True,
        verbose_name=_('Message from'), default=DEFAULT_FROM_EMAIL,
        help_text=_('If not specified, then used default.'),
        on_delete=models.SET_NULL)
    bcc_email = models.ManyToManyField(
        MailBcc, verbose_name=_('Bcc'), blank=True,
        help_text='Blind carbon copy')
    message = HTMLField(_('Body'))
    slug = models.SlugField(
        _('Slug'), unique=True,
        help_text=_('Unique slug to use in code.'))
    num_of_retries = models.PositiveIntegerField(
        _('Number of retries'), default=1)
    priority = models.SmallIntegerField(
        _('Priority'), default=DEFAULT_PRIORITY, choices=PRIORITY_STEPS)
    is_html = models.BooleanField(
        _('Is html'), default=True,
        help_text=_('For sms/tts/push must be text not html'))
    is_admin = models.BooleanField(_('For admin'), default=False)
    is_active = models.BooleanField(_('Is active'), default=True)
    enable_log = models.BooleanField(_('Logging enabled'), default=True)
    category = models.ForeignKey(
        MailCategory, null=True, blank=True,
        verbose_name=_('Category'), default=DEFAULT_CATEGORY)
    base = models.ForeignKey(
        MailBaseTemplate, null=True, blank=True,
        verbose_name=_('Basic template'))
    created = models.DateTimeField(_('Created'), auto_now_add=True)
    updated = models.DateTimeField(_('Updated'), auto_now=True)
    context_note = models.TextField(
        _('Context note'), null=True, blank=True,
        help_text=_(
            'This is simple note field for context variables with description.'
        )
    )
    interval = models.PositiveIntegerField(
        _('Send interval'), null=True, blank=True,
        help_text=_(
            """
            Specify interval to send messages after sometime.
            Interval must be set in the seconds.
            """
        ))

    def _clean_cache(self):
        cache.delete(self.slug, version=1)

    @classmethod
    def clean_cache(cls, **kwargs):
        for template in cls.objects.filter(**kwargs):
            template._clean_cache()

    def _clean_non_html(self):
        if not self.is_html:
            self.message = strip_tags(self.message)
            if hasattr(settings, 'MODELTRANSLATION_LANGUAGES'):
                for lang in settings.MODELTRANSLATION_LANGUAGES:
                    message = strip_tags(getattr(self, 'message_%s' % lang))
                    if message:
                        setattr(self, 'message_%s' % lang, message)

    def _premailer_transform(self):
        if self.is_html:
            self.message = premailer_transform(self.message)

    @classmethod
    def get_template(cls, slug):
        obj = cache.get(slug, version=1)

        if obj is not None:
            return obj

        obj = cls.objects.select_related('from_email', 'base').get(slug=slug)
        bcc_list = [o.email for o in obj.bcc_email.filter(is_active=1)]
        files_list = list(obj.files.all())
        auth_credentials = obj.from_email and obj.from_email.get_auth()

        obj.__dict__['bcc_list'] = bcc_list
        obj.__dict__['files_list'] = files_list
        obj.__dict__['auth_credentials'] = auth_credentials

        cache.set(slug, obj, timeout=CACHE_TTL, version=1)

        return obj

    def save(self, *args, **kwargs):
        self._premailer_transform()
        self._clean_non_html()
        self.slug = re.sub(r'[^0-9a-zA-Z._-]', '', self.slug)
        super(MailTemplate, self).save(*args, **kwargs)
        self._clean_cache()

    def delete(self, using=None):
        self._clean_cache()
        super(MailTemplate, self).delete(using)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = _('Mail template')
        verbose_name_plural = _('Mail templates')


@python_2_unicode_compatible
class MailFile(models.Model):
    template = models.ForeignKey(
        MailTemplate, verbose_name=_('Template'), related_name='files')
    name = models.CharField(_('Name'), max_length=100)
    filename = models.FileField(_('File'), upload_to=_upload_mail_file)

    def _clean_cache(self):
        MailTemplate.clean_cache(pk=self.template.pk)

    def save(self, *args, **kwargs):
        super(MailFile, self).save(*args, **kwargs)
        self._clean_cache()

    def delete(self, using=None):
        self._clean_cache()
        super(MailFile, self).delete(using)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = _('Mail file')
        verbose_name_plural = _('Mail files')


@python_2_unicode_compatible
class MailLogException(models.Model):
    name = models.CharField(_('Exception'), max_length=150, unique=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = _('Mail Exception')
        verbose_name_plural = _('Mail Exception')


@python_2_unicode_compatible
class MailLog(models.Model):
    is_sent = models.BooleanField(_('Is sent'), default=True, db_index=True)
    template = models.ForeignKey(MailTemplate, verbose_name=_('Template'))
    created = models.DateTimeField(_('Created'), auto_now_add=True)
    user = models.ForeignKey(
        AUTH_USER_MODEL, verbose_name=_('User'),
        null=True, blank=True)
    error_message = models.TextField(_('Error message'), null=True, blank=True)
    error_exception = models.ForeignKey(
        MailLogException, null=True, blank=True, verbose_name=_('Exception'))
    num_of_retries = models.PositiveIntegerField(
        _('Number of retries'), default=1)
    log_id = models.CharField(
        _('Log ID'), max_length=60, editable=False, db_index=True)
    backend = models.CharField(
        _('Backend'), max_length=25, editable=False, db_index=True,
        choices=BACKEND.items(), default='mail')
    provider = models.CharField(
        _('Provider'), max_length=250, editable=False, db_index=True,
        default=None, null=True, blank=True)

    @staticmethod
    def store_email_log(log, email_list, mail_type):
        if log and email_list:
            for email in email_list:
                MailLogEmail.objects.create(
                    log=log, email=email, mail_type=mail_type
                )

    @classmethod
    def store(cls, to, cc, bcc, is_sent, template,
              user, num, msg='', ex=None, log_id=None,
              backend=None, provider=None):
        if ex is not None:
            ex = MailLogException.objects.get_or_create(name=ex)[0]

        log = cls.objects.create(
            template=template, is_sent=is_sent, user=user,
            log_id=log_id, num_of_retries=num, error_message=msg,
            error_exception=ex, backend=_BACKEND.get(backend, backend),
            provider=provider
        )
        cls.store_email_log(log, to, 'to')
        cls.store_email_log(log, cc, 'cc')
        cls.store_email_log(log, bcc, 'bcc')

    @classmethod
    def cleanup(cls, days=7):
        date = now() - datetime.timedelta(days=days)
        cls.objects.filter(created__lte=date).delete()

    def __str__(self):
        return self.template.name

    class Meta:
        verbose_name = _('Mail log')
        verbose_name_plural = _('Mail logs')


@python_2_unicode_compatible
class MailLogEmail(models.Model):
    log = models.ForeignKey(MailLog)
    email = models.CharField(_('Recipient'), max_length=75)
    mail_type = models.CharField(_('Mail type'), choices=(
        ('cc', 'CC'),
        ('bcc', 'BCC'),
        ('to', 'TO'),
    ), max_length=3)

    def __str__(self):
        return self.email

    class Meta:
        verbose_name = _('Mail log email')
        verbose_name_plural = _('Mail log emails')


@python_2_unicode_compatible
class MailGroup(models.Model):
    name = models.CharField(_('Group name'), max_length=100)
    slug = models.SlugField(_('Slug'), unique=True)
    created = models.DateTimeField(_('Created'), auto_now_add=True)
    updated = models.DateTimeField(_('Updated'), auto_now=True)

    def clean_cache(self):
        cache.delete(self.slug, version=4)

    @classmethod
    def get_emails(cls, slug):
        emails = cache.get(slug, version=4)

        if emails is not None:
            return emails

        emails = MailGroupEmail.objects.values_list(
            'email', flat=True).filter(group__slug=slug)

        cache.set(slug, emails, timeout=CACHE_TTL, version=4)
        return emails

    def save(self, *args, **kwargs):
        self.slug = re.sub(r'[^0-9a-zA-Z._-]', '', self.slug)
        super(MailGroup, self).save(*args, **kwargs)
        self.clean_cache()

    def delete(self, using=None):
        self.clean_cache()
        super(MailGroup, self).delete(using)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = _('Mail group')
        verbose_name_plural = _('Mail groups')


@python_2_unicode_compatible
class MailGroupEmail(models.Model):
    name = models.CharField(_('Username'), max_length=100)
    email = models.CharField(
        _('Email'), max_length=75,
        help_text='For sms/tts you must specify number')
    group = models.ForeignKey(
        MailGroup, verbose_name=_('Group'), related_name='emails')

    def save(self, *args, **kwargs):
        super(MailGroupEmail, self).save(*args, **kwargs)
        self.group.clean_cache()

    def delete(self, using=None):
        self.group.clean_cache()
        super(MailGroupEmail, self).delete(using)

    def __str__(self):
        return self.email

    class Meta:
        verbose_name = _('Mail group email')
        verbose_name_plural = _('Mail group emails')
        unique_together = (('email', 'group',),)


@python_2_unicode_compatible
class Signal(models.Model):
    SIGNALS = (
        'pre_save',
        'post_save',
        'pre_delete',
        'post_delete',
        'm2m_changed',
    )
    name = models.CharField(_('Name'), max_length=100)
    model = models.ForeignKey(
        'contenttypes.ContentType', verbose_name=_('Model'))
    signal = models.CharField(
        _('Signal'), choices=zip(SIGNALS, SIGNALS),
        max_length=15, default='post_save')
    template = models.ForeignKey(MailTemplate, verbose_name=_('Template'))
    group = models.ForeignKey(
        MailGroup, verbose_name=_('Email group'), blank=True, null=True,
        help_text=_('You can use group email or rules for recipients.'))
    rules = models.TextField(
        help_text=_(
            'Template should return email to send message. Example:'
            '{% if instance.is_active %}{{ instance.email }}{% endif %}.'
            'You can return a multiple emails separated by commas.'
        ), default='{{ instance.email }}', verbose_name=_('Rules'),
        null=True, blank=True
    )
    created = models.DateTimeField(_('Created'), auto_now_add=True)
    updated = models.DateTimeField(_('Updated'), auto_now=True)
    is_active = models.BooleanField(_('Is active'), default=True)
    receive_once = models.BooleanField(
        _('Receive once'), default=True,
        help_text=_('Signal will be receive and send once for new db row.'))
    interval = models.PositiveIntegerField(
        _('Send interval'), null=True, blank=True,
        help_text=_(
            'Specify interval to send messages after sometime. '
            'That very helpful for mailing on enterprise products.'
            'Interval must be set in the seconds.'
        ))
    update_model = models.BooleanField(
        _('Update model state'), default=False,
        help_text=_(
            """
            If you are using interval and want to update object state,
            you can use this flag and refer to the variable
            {{current_instance}}
            """))

    def is_sent(self, pk):
        if pk is not None:
            if self.receive_once is True:
                return SignalLog.objects.filter(
                    model=self.model, model_pk=pk, signal=self).exists()
            return False

    def mark_as_sent(self, pk):
        if pk is not None:
            SignalLog.objects.create(
                model=self.model, model_pk=pk, signal=self
            )

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = _('Mail signal')
        verbose_name_plural = _('Mail signals')


@python_2_unicode_compatible
class SignalLog(models.Model):
    model = models.ForeignKey('contenttypes.ContentType')
    model_pk = models.BigIntegerField()
    signal = models.ForeignKey(Signal)
    created = models.DateTimeField(_('Created'), auto_now_add=True)

    def __str__(self):
        return self.signal.name

    class Meta:
        verbose_name = _('Signal log')
        verbose_name_plural = _('Signal logs')


class SignalDeferredDispatch(models.Model):
    args = models.TextField()
    kwargs = models.TextField()
    params = models.TextField()
    eta = models.DateTimeField(db_index=True)
    done = models.NullBooleanField(default=None)
    created = models.DateTimeField(auto_now_add=True)

    def run_task(self):
        if self.done is False:
            import tasks

            tasks.deferred_signal.apply_async(
                args=pickle.loads(self.args),
                kwargs=pickle.loads(self.kwargs),
                **pickle.loads(self.params)
            )

    @classmethod
    def add_task(cls, args, kwargs, params, interval):
        eta = now() + datetime.timedelta(seconds=interval)
        dump = pickle.dumps
        return cls.objects.create(
            args=dump(args), kwargs=dump(kwargs),
            params=dump(params), eta=eta
        )

    class Meta:
        if VERSION >= (1, 5):
            index_together = (('eta', 'done'),)


@python_2_unicode_compatible
class ApiKey(models.Model):
    name = models.CharField(_('Name'), max_length=25)
    api_key = models.CharField(_('Api key'), max_length=32, unique=True)
    is_active = models.BooleanField(_('Is active'), default=True)
    created = models.DateTimeField(_('Created'), auto_now_add=True)
    updated = models.DateTimeField(_('Updated'), auto_now=True)

    def _clean_cache(self):
        cache.delete(self.api_key)

    @classmethod
    def clean_cache(cls):
        for api in cls.objects.all():
            api._clean_cache()

    def save(self, *args, **kwargs):
        super(ApiKey, self).save(*args, **kwargs)
        self._clean_cache()

    def delete(self, using=None):
        self._clean_cache()
        super(ApiKey, self).delete(using)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = _('Mail API')
        verbose_name_plural = _('Mail API')


@python_2_unicode_compatible
class MailLogTrack(models.Model):
    mail_log = models.ForeignKey(MailLog, verbose_name=_('Log'))
    counter = models.PositiveIntegerField(_('Counter'), default=0)
    ip = models.GenericIPAddressField(_('IP'))
    ua = models.CharField(
        _('User Agent'), max_length=350, blank=True, null=True)

    ua_os = models.CharField(_('OS'), max_length=100, blank=True, null=True)
    ua_os_version = models.CharField(
        _('OS version'), max_length=100, blank=True, null=True)

    ua_dist = models.CharField(
        _('Dist name'), max_length=20, blank=True, null=True)
    ua_dist_version = models.CharField(
        _('Dist version'), max_length=100, blank=True, null=True)
    ua_browser = models.CharField(
        _('Browser'), max_length=100, blank=True, null=True)
    ua_browser_version = models.CharField(
        _('Browser version'), max_length=20, blank=True, null=True)
    ip_area_code = models.CharField(
        _('Area code'), max_length=255, blank=True, null=True)
    ip_city = models.CharField(
        _('City'), max_length=255, blank=True, null=True)
    ip_country_code = models.CharField(
        _('Country code'), max_length=255, blank=True, null=True)
    ip_country_code3 = models.CharField(
        _('Country code3'), max_length=255, blank=True, null=True)
    ip_country_name = models.CharField(
        _('Country name'), max_length=255, blank=True, null=True)
    ip_dma_code = models.CharField(
        _('Dma code'), max_length=255, blank=True, null=True)
    ip_latitude = models.CharField(
        _('Latitude'), max_length=255, blank=True, null=True)
    ip_longitude = models.CharField(
        _('Longitude'), max_length=255, blank=True, null=True)
    ip_postal_code = models.CharField(
        _('Postal code'), max_length=255, blank=True, null=True)
    ip_region = models.CharField(
        _('Region'), max_length=255, blank=True, null=True)

    is_read = models.BooleanField(_('Is read'), default=False)
    created = models.DateTimeField(_('Created'), auto_now_add=True)
    updated = models.DateTimeField(_('Updated'), auto_now=True)

    def __str__(self):
        return self.mail_log.template.name

    class Meta:
        verbose_name = _('Mail Tracking')
        verbose_name_plural = _('Mail Tracking')

    def detect_ua(self):
        try:
            if self.ua and self.counter == 0:
                import httpagentparser

                data = httpagentparser.detect(self.ua)
                get = lambda b, k: data.get(b, {}).get(k, '')

                self.ua_os = get('os', 'name')
                self.ua_os_version = get('os', 'version')

                self.ua_dist = get('platform', 'name')
                self.ua_dist_version = get('platform', 'version')

                self.ua_browser = get('browser', 'name')
                self.ua_browser_version = get('browser', 'version')

        except ImportError:
            pass

    def detect_geo(self):
        if self.ip and self.counter == 0:
            from django.contrib.gis.geoip import GeoIP, GeoIPException

            try:
                g = GeoIP()
                info = g.city(self.ip) or dict()
                for (k, v) in info.items():
                    setattr(self, 'ip_%s' % k, v)
            except GeoIPException:
                pass

    def detect_open(self):
        if self.counter == 0:
            self.counter = 1
        elif self.counter >= 1:
            self.counter += 1

    def save(self, *args, **kwargs):
        self.detect_ua()
        self.detect_geo()
        self.detect_open()
        super(MailLogTrack, self).save(*args, **kwargs)


class MailSubscriptionAbstract(models.Model):
    user = models.ForeignKey(
        AUTH_USER_MODEL, verbose_name=_('User'), null=True, blank=True)
    backend = models.CharField(
        _('Backend'), choices=BACKENDS_MODEL_CHOICES, max_length=50,
        default=BACKEND.get('mail'))
    start_hour = models.CharField(
        _('Start hour'), default='00:00', max_length=5)
    end_hour = models.CharField(_('End hour'), default='23:59', max_length=5)
    is_enabled = models.BooleanField(
        _('Is enabled'), default=True, db_index=True)
    is_checked = models.BooleanField(
        _('Is checked'), default=False, db_index=True)
    defer_at_allowed_hours = models.BooleanField(
        _('Defer at allowed hours'), default=False)
    address = models.CharField(
        _('Address'), max_length=60, db_index=True,
        help_text=_('Must be phone number/email/token'))

    def send_confirmation_link(
            self, slug='subs-confirmation', *args, **kwargs):

        from dbmail import db_sender

        kwargs['backend'] = self.backend
        db_sender(slug, self.address, *args, **kwargs)

    @staticmethod
    def get_now():
        return timezone.localtime(timezone.now())

    @staticmethod
    def get_current_hour():
        current = timezone.localtime(timezone.now())
        return datetime.timedelta(hours=current.hour, minutes=current.minute)

    @staticmethod
    def convert_to_date(value):
        hour, minute = value.split(':')
        return datetime.timedelta(hours=int(hour), minutes=int(minute))

    @classmethod
    def mix_hour_with_date(cls, value):
        return datetime.datetime.strptime(
            cls.get_now().strftime('%Y-%m-%d ') + value, '%Y-%m-%d %H:%M')

    @classmethod
    def get_notification_list(cls, user_id, **kwargs):
        kwargs.update({
            'is_enabled': True,
            'is_checked': True,
        })
        if user_id is not None:
            kwargs.update({
                'user_id': user_id,
            })
        return cls.objects.filter(**kwargs)

    @classmethod
    def notify(cls, slug, user_id=None, sub_filter=None, **kwargs):

        from dbmail import db_sender

        now_hour = cls.get_current_hour()

        context_dict = kwargs.pop('context', {})
        context_instance = kwargs.pop('context_instance', None)

        sub_filter = sub_filter if isinstance(sub_filter, dict) else {}

        for method in cls.get_notification_list(user_id, **sub_filter):
            kwargs['send_at_date'] = None
            start_hour = cls.convert_to_date(method.start_hour)
            end_hour = cls.convert_to_date(method.end_hour)

            if not (start_hour <= now_hour <= end_hour):
                if method.defer_at_allowed_hours and kwargs['use_celery']:
                    kwargs['send_at_date'] = cls.mix_hour_with_date(
                        method.start_hour)
                else:
                    continue
            kwargs['backend'] = method.backend

            extra_slug = '%s-%s' % (slug, method.get_short_type())
            use_slug = slug

            kwargs = method.update_notify_kwargs(**kwargs)
            try:
                if MailTemplate.get_template(slug=extra_slug):
                    use_slug = extra_slug
            except MailTemplate.DoesNotExist:
                pass
            db_sender(use_slug, method.address, context_dict,
                      context_instance, **kwargs)

    def update_notify_kwargs(self, **kwargs):
        return kwargs

    def get_short_type(self):
        return self.backend.split('.')[-1]

    class Meta:
        abstract = True


@python_2_unicode_compatible
class MailSubscription(MailSubscriptionAbstract):
    class Meta:
        verbose_name = _('Mail Subscription')
        verbose_name_plural = _('Mail Subscriptions')

    def __str__(self):
        if self.user:
            return self.user.username
        return self.address

'''
class MailSubscriptionGroup(models.Model):
    group = models.CharField(max_length=100, unique=True)


class MailNotification(models.Model):
    group = models.ForeignKey(AbstractMailSubscriptionGroup)
    notify = models.ManyToManyField(MailSubscription)

    @classmethod
    def notify(cls, user, mail_slug, group, **kwargs):
        from dbmail import send_db_subscription

        for notify in cls.objects.filter(notify__user=user, group=group):
            send_db_subscription(
                mail_slug, user.pk, {'pk': notify.pk}, **kwargs)
'''

if VERSION < (1, 7):
    initial_signals()
