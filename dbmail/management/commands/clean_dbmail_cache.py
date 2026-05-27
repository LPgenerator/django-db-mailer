from __future__ import annotations

from django.core.management.base import BaseCommand

from dbmail.models import ApiKey, MailTemplate


class Command(BaseCommand):
    def handle(self, *args, **options):
        MailTemplate.clean_cache()
        ApiKey.clean_cache()
