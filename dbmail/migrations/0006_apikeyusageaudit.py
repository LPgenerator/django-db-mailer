"""Create :class:`ApiKeyUsageAudit` for the public API endpoint (ADR-0006).

Tracks every authentication/authorisation decision made by
``dbmail.views.send_by_dbmail`` so operators can answer "who sent what
from where" without ELK. The FK to :class:`ApiKey` uses ``PROTECT`` —
deleting an ApiKey requires the operator to acknowledge any retained
audit history first.
"""

from __future__ import annotations

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("dbmail", "0005_signal_dotted_paths"),
    ]

    operations = [
        migrations.CreateModel(
            name="ApiKeyUsageAudit",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True, primary_key=True, serialize=False, verbose_name="ID"
                    ),
                ),
                ("api_key_name", models.CharField(blank=True, max_length=25, null=True, verbose_name="API key name")),
                ("ip", models.CharField(blank=True, max_length=45, null=True, verbose_name="IP")),
                ("ua", models.CharField(blank=True, max_length=512, null=True, verbose_name="User-Agent")),
                ("action", models.CharField(db_index=True, max_length=32, verbose_name="Action")),
                ("success", models.BooleanField(default=False, verbose_name="Success")),
                ("detail", models.CharField(blank=True, max_length=255, null=True, verbose_name="Detail")),
                ("created", models.DateTimeField(auto_now_add=True, db_index=True, verbose_name="Created")),
                (
                    "api_key",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.PROTECT,
                        to="dbmail.apikey",
                        verbose_name="API key",
                    ),
                ),
            ],
            options={
                "verbose_name": "API key usage audit",
                "verbose_name_plural": "API key usage audit",
                "ordering": ("-created",),
            },
        ),
    ]
