from django.core.management.base import BaseCommand
from dbmail.models import MailTemplate, ApiKey


class Command(BaseCommand):
    def handle(self, *args, **options):
        MailTemplate.clean_cache()
        ApiKey.clean_cache()
