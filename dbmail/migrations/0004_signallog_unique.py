"""Make ``SignalLog`` idempotent under concurrent Celery workers.

``Signal.is_sent()`` + ``Signal.mark_as_sent()`` formed a classic
check-then-act race: two workers could pass the ``EXISTS`` probe and
both ``INSERT`` a row, causing duplicate deliveries for
``receive_once`` signals. The unique constraint on
``(model, model_pk, signal)`` lets the database enforce uniqueness;
``mark_as_sent()`` now swallows :class:`IntegrityError` from the
losing worker. See ADR-0011 / H3.
"""

from __future__ import annotations

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("dbmail", "0003_maillog_correlation_id"),
    ]

    operations = [
        migrations.AddConstraint(
            model_name="signallog",
            constraint=models.UniqueConstraint(
                fields=("model", "model_pk", "signal"),
                name="dbmail_signallog_unique_send",
            ),
        ),
    ]
