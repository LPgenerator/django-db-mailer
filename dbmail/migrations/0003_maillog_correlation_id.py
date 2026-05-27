"""Add ``MailLog.correlation_id`` for distributed-tracing tags.

See ADR-0011. The column is nullable and indexed so existing
``MailLog`` rows upgrade without backfill. Senders may pass
``correlation_id="..."`` (max 64 chars) via :func:`send_db_mail` and
friends to attach a business key (``order_id``, ``request_id``, W3C
``traceparent`` fragment) to each delivery attempt.
"""

from __future__ import annotations

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("dbmail", "0002_apikey_hash_data"),
    ]

    operations = [
        migrations.AddField(
            model_name="maillog",
            name="correlation_id",
            field=models.CharField(
                blank=True,
                db_index=True,
                help_text="Business correlation key (e.g. order_id, request_id).",
                max_length=64,
                null=True,
                verbose_name="Correlation ID",
            ),
        ),
    ]
