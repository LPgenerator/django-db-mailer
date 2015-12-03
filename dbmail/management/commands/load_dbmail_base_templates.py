from django.core.management.base import BaseCommand
from django.core.management import call_command


class Command(BaseCommand):
    def handle(self, *args, **options):
        call_command('loaddata', 'mailgun_base_templates', app_label='dbmail')
