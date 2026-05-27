from __future__ import annotations

import logging

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils.timezone import now

from dbmail.defaults import SIGNAL_DB_DEFERRED_PURGE
from dbmail.models import SignalDeferredDispatch

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Dispatch due deferred dbmail signals (cron-driven, idempotent under concurrency)."

    def add_arguments(self, parser):
        parser.add_argument(
            "--limit",
            type=int,
            default=500,
            help="Max number of deferred signals to dispatch in one run.",
        )

    def handle(self, *args, **options):
        limit = options["limit"]
        processed = 0
        while processed < limit:
            row_pk = self._claim_one()
            if row_pk is None:
                break
            self._dispatch(row_pk)
            processed += 1
        if processed:
            logger.info("send_dbmail_deferred_signal: dispatched %s rows", processed)

    @staticmethod
    def _claim_one() -> int | None:
        with transaction.atomic():
            row = (
                SignalDeferredDispatch.objects.select_for_update(skip_locked=True)
                .filter(done__isnull=True, eta__lte=now())
                .order_by("eta")
                .only("pk")
                .first()
            )
            if row is None:
                return None
            SignalDeferredDispatch.objects.filter(pk=row.pk).update(done=False)
            return row.pk

    @staticmethod
    def _dispatch(pk: int) -> None:
        try:
            row = SignalDeferredDispatch.objects.get(pk=pk)
        except SignalDeferredDispatch.DoesNotExist:
            return
        try:
            row.run_task()
        except Exception:
            logger.exception("send_dbmail_deferred_signal: row pk=%s failed", pk)
            return
        if SIGNAL_DB_DEFERRED_PURGE is True:
            SignalDeferredDispatch.objects.filter(pk=pk).delete()
        else:
            SignalDeferredDispatch.objects.filter(pk=pk).update(done=True)
