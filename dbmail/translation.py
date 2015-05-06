# -*- encoding: utf-8 -*-

from modeltranslation.translator import translator, TranslationOptions
from dbmail.models import MailTemplate, MailBaseTemplate


class MailTemplateTranslationOptions(TranslationOptions):
    fields = ('subject', 'message',)


class MailBaseTemplateTranslationOptions(TranslationOptions):
    fields = ('message',)

translator.register(MailTemplate, MailTemplateTranslationOptions)
translator.register(MailBaseTemplate, MailBaseTemplateTranslationOptions)
