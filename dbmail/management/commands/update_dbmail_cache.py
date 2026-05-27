from __future__ import annotations

from django.core.management.base import BaseCommand

from dbmail.models import MailTemplate


class Command(BaseCommand):
    help = "Wipe and rewarm the MailTemplate cache."

    def handle(self, *args, **options):
        MailTemplate.clean_cache()
        for slug in MailTemplate.objects.values_list("slug", flat=True):
            MailTemplate.get_template(slug)
