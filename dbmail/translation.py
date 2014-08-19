# -*- encoding: utf-8 -*-

from modeltranslation.translator import translator, TranslationOptions
from dbmail.models import MailTemplate


class MailTemplateTranslationOptions(TranslationOptions):
    fields = ('subject', 'message',)

translator.register(MailTemplate, MailTemplateTranslationOptions)
