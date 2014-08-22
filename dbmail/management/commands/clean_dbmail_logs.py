from django.core.management.base import BaseCommand
from dbmail.defaults import LOGS_EXPIRE_DAYS
from dbmail.models import MailLog


class Command(BaseCommand):
    def handle(self, *args, **options):
        MailLog.cleanup(days=LOGS_EXPIRE_DAYS)
