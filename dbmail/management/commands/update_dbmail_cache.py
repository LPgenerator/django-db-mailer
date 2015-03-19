from django.core.management.base import BaseCommand
from dbmail.models import MailTemplate


class Command(BaseCommand):
    def handle(self, *args, **options):
        for obj in MailTemplate.objects.all():
            MailTemplate.clean_cache()
            MailTemplate.get_template(obj.slug)
