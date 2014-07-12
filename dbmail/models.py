# -*- encoding: utf-8 -*-

from django.utils.translation import ugettext_lazy as _
from django.utils.html import strip_tags
from django.core.cache import cache
from django.conf import settings
from django.db import models

from dbmail.defaults import PRIORITY_STEPS
from dbmail.fields import HTMLField


class MailCategory(models.Model):
    name = models.CharField(_('Category'), max_length=25)
    created = models.DateTimeField(_('Created'), auto_now_add=True)
    updated = models.DateTimeField(_('Updated'), auto_now=True)

    def __unicode__(self):
        return self.name

    class Meta:
        verbose_name = _('Category')
        verbose_name_plural = _('Categories')


class MailTemplate(models.Model):
    name = models.CharField(_('Template name'), max_length=100)
    subject = models.CharField(_('Subject'), max_length=100)
    message = HTMLField(_('Body'))
    slug = models.SlugField(_('Slug'), unique=True)
    num_of_retries = models.PositiveIntegerField(
        _('Number of retries'), default=1)
    priority = models.SmallIntegerField(
        _('Priority'),  default=0,
        choices=zip(reversed(PRIORITY_STEPS), PRIORITY_STEPS),
        help_text=_(
            'A number between 0 and 9, where 9 is the highest priority.'
        ))
    is_html = models.BooleanField(_('Is html'), default=False)
    is_admin = models.BooleanField(_('For admin'), default=False)
    category = models.ForeignKey(
        MailCategory, null=True, blank=True,
        verbose_name=_('Category'))
    created = models.DateTimeField(_('Created'), auto_now_add=True)
    updated = models.DateTimeField(_('Updated'), auto_now=True)

    def save(self, *args, **kwargs):
        if not self.is_html:
            self.message = strip_tags(self.message)
        cache.delete(self.slug)
        return super(MailTemplate, self).save(*args, **kwargs)

    def __unicode__(self):
        return self.name

    class Meta:
        verbose_name = _('Mail template')
        verbose_name_plural = _('Mail templates')

    @classmethod
    def get_template(cls, slug):
        obj = cache.get(slug)
        if obj is not None:
            return obj
        else:
            obj = cls.objects.get(slug=slug)
            cache.set(slug, obj)
            return obj


class MailLog(models.Model):
    is_sent = models.BooleanField(_('Is sent'), default=True)
    template = models.ForeignKey(MailTemplate, verbose_name=_('Template'))
    created = models.DateTimeField(_('Created'), auto_now_add=True)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, verbose_name=_('User'),
        null=True, blank=True)
    error_message = models.TextField(_('Error message'), null=True, blank=True)
    num_of_retries = models.PositiveIntegerField(
        _('Number of retries'), default=1)

    def __unicode__(self):
        return self.template.name

    class Meta:
        verbose_name = _('Mail log')
        verbose_name_plural = _('Mail logs')

    @staticmethod
    def store_email_log(log, email_list, mail_type):
        if log and email_list:
            for email in email_list:
                MailLogEmail.objects.create(
                    log=log, email=email, mail_type=mail_type
                )

    @classmethod
    def store(cls, to, cc, bcc, is_sent, template, user, num, message=None):
        log = cls.objects.create(
            template=template, is_sent=is_sent, user=user,
            num_of_retries=num, error_message=message
        )
        cls.store_email_log(log, to, 'to')
        cls.store_email_log(log, cc, 'cc')
        cls.store_email_log(log, bcc, 'bcc')


class MailLogEmail(models.Model):
    log = models.ForeignKey(MailLog)
    email = models.EmailField()
    mail_type = models.CharField(_('Mail type'), choices=(
        ('cc', 'CC'),
        ('bcc', 'BCC'),
        ('to', 'TO'),
    ), max_length=3)

    def __unicode__(self):
        return self.email

    class Meta:
        verbose_name = _('Mail log email')
        verbose_name_plural = _('Mail log emails')
