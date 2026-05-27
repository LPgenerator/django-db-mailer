# Schedule deferred sends from signals

A welcome email could fire 5 minutes after signup so the user is
likely past the onboarding flow when it arrives. Or a "review request"
email scheduled 7 days after order delivery.

`dbmail` supports this through `Signal.interval` — the number of
seconds to wait before the actual send. When `interval > 0`, the
signal handler does **not** dispatch immediately; instead, it writes
a row to `SignalDeferredDispatch`, and a periodic worker drains the
queue when `eta <= now()`.

## Configure

1. Open `/admin/dbmail/signal/<id>/change/` (or create a new Signal).
2. Set **Interval** to the delay in seconds (`300` = 5 minutes,
   `604800` = 7 days).
3. Save. Existing dispatch_uid stays connected; only the handling
   path changes (deferred instead of immediate).

## Run the drainer

```bash
python manage.py send_dbmail_deferred_signal --limit 500
```

Schedule this with cron (every minute) or Celery beat:

```python
# Celery beat
CELERY_BEAT_SCHEDULE = {
    "dbmail-deferred-signal": {
        "task": "dbmail.deferred_signal",
        "schedule": 60.0,
    },
}
```

…or actually invoke the management command from beat via
`django.core.management.call_command`:

```python
from celery import shared_task
from django.core.management import call_command

@shared_task(name="dbmail.deferred_drainer")
def deferred_drainer():
    call_command("send_dbmail_deferred_signal", limit=500)
```

## Concurrency safety

The drainer uses `select_for_update(skip_locked=True)` on PostgreSQL
and MySQL ≥ 8 — multiple parallel runs will not double-fire a row.

SQLite does **not** honor `skip_locked` and will fall back to lock
contention; it works for development but is not recommended at
production load.

## Inspecting the queue

```python
from dbmail.models import SignalDeferredDispatch
from django.utils import timezone

# Pending rows that should already have fired (drainer is behind)
SignalDeferredDispatch.objects.filter(
    done__isnull=True,
    eta__lte=timezone.now(),
).count()

# Future rows (scheduled ahead)
SignalDeferredDispatch.objects.filter(
    done__isnull=True,
    eta__gt=timezone.now(),
).order_by("eta").values_list("eta", flat=True)[:20]

# Already-dispatched (kept until DB_MAILER_SIGNAL_DB_DEFERRED_PURGE
# decides — default `True` deletes after dispatch)
SignalDeferredDispatch.objects.filter(done=True).count()
```

## Removing a scheduled row

If the user unsubscribes between scheduling and the eta:

```python
SignalDeferredDispatch.objects.filter(
    done__isnull=True,
    args_json__contains=[user_email],
).delete()
```

`args_json` was added in 3.0 as part of the pickle → JSON migration. Pre-3.0
rows used pickle; if you have legacy rows enable
`DB_MAILER_ALLOW_PICKLE_LEGACY = True` explicitly — see
[security model](../explanation/security.md).

## Settings

| Setting | Default | Purpose |
|---|---|---|
| `DB_MAILER_SIGNAL_DEFERRED_DISPATCHER` | `"celery"` | `"celery"` or `"db"` — choose the queue backend. `"db"` writes `SignalDeferredDispatch` rows; `"celery"` uses `apply_async(eta=...)`. |
| `DB_MAILER_SIGNAL_DB_DEFERRED_PURGE` | `True` | If `True`, dispatched rows are deleted after success. If `False`, rows are kept with `done=True` for audit. |
| `DB_MAILER_ALLOW_PICKLE_LEGACY` | `False` | Opt-in for legacy pickle-blob rows. Required when migrating data from a 2.x install (rare; clean-break is preferred). |

## See also

- [reference/models.md](../reference/models.md#signaldeferreddispatch)
  — schema.
- [getting_started/03_signals.md](../getting_started/03_signals.md) —
  basic Signal tutorial.
- [Security model](../explanation/security.md) — pickle gating.
