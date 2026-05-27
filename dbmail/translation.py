from modeltranslation.translator import TranslationOptions, translator

from dbmail.models import MailBaseTemplate, MailTemplate


class MailTemplateTranslationOptions(TranslationOptions):
    fields = (
        "subject",
        "message",
    )


class MailBaseTemplateTranslationOptions(TranslationOptions):
    fields = ("message",)


translator.register(MailTemplate, MailTemplateTranslationOptions)
translator.register(MailBaseTemplate, MailBaseTemplateTranslationOptions)
