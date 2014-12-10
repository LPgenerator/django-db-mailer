from django.core.management.base import BaseCommand
from django.utils.timezone import now

from dbmail.defaults import SIGNAL_DB_DEFERRED_PURGE
from dbmail.models import SignalDeferredDispatch


class Command(BaseCommand):
    def __init__(self):
        super(Command, self).__init__()
        self.signal = None

    def done(self):
        if SIGNAL_DB_DEFERRED_PURGE is True:
            self.signal.delete()
        else:
            self.signal.done = True
            self.signal.save()

    def start(self):
        self.signal.done = False
        self.signal.save()

    @staticmethod
    def signals():
        return SignalDeferredDispatch.objects.filter(
            done__isnull=True, eta__lte=now())

    def handle(self, *args, **options):
        for self.signal in self.signals():
            self.start()
            self.signal.run_task()
            self.done()
