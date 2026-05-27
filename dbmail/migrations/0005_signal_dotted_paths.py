"""Widen ``Signal.signal`` to dotted paths and backfill legacy rows.

Old schema (2.5 / 3.0) stored Django built-in signal short names
(``post_save``, ``pre_delete`` …) in a ``CharField(max_length=15)``.
That model is closed: operators could not wire custom signals such as
``myapp.signals.order_paid``. C2 widens the column to ``max_length=255``
and rewrites stored values to fully-qualified dotted paths resolvable
through ``import_string``. Settings hook:
``DB_MAILER_SIGNAL_CHOICES``.

The data migration is reversible — the reverse path maps each known
``django.db.models.signals.*`` value back to its short name and leaves
any operator-defined dotted paths untouched (a downgrade with custom
signals will fail the old ``max_length=15`` check, which is the
intended signal to the operator that those rows need attention).
"""

from __future__ import annotations

from django.db import migrations, models

from dbmail.defaults import SIGNAL_CHOICES

_FORWARD_MAPPING = {
    "post_save": "django.db.models.signals.post_save",
    "pre_save": "django.db.models.signals.pre_save",
    "post_delete": "django.db.models.signals.post_delete",
    "pre_delete": "django.db.models.signals.pre_delete",
    "m2m_changed": "django.db.models.signals.m2m_changed",
}
_REVERSE_MAPPING = {v: k for k, v in _FORWARD_MAPPING.items()}


def _forward(apps, schema_editor):
    Signal = apps.get_model("dbmail", "Signal")
    db_alias = schema_editor.connection.alias
    for row in Signal.objects.using(db_alias).iterator():
        new = _FORWARD_MAPPING.get(row.signal)
        if new and new != row.signal:
            Signal.objects.using(db_alias).filter(pk=row.pk).update(signal=new)


def _reverse(apps, schema_editor):
    Signal = apps.get_model("dbmail", "Signal")
    db_alias = schema_editor.connection.alias
    for row in Signal.objects.using(db_alias).iterator():
        old = _REVERSE_MAPPING.get(row.signal)
        if old and old != row.signal:
            Signal.objects.using(db_alias).filter(pk=row.pk).update(signal=old)


class Migration(migrations.Migration):
    dependencies = [
        ("dbmail", "0004_signallog_unique"),
    ]

    operations = [
        migrations.AlterField(
            model_name="signal",
            name="signal",
            field=models.CharField(
                choices=SIGNAL_CHOICES,
                default="django.db.models.signals.post_save",
                max_length=255,
                verbose_name="Signal",
            ),
        ),
        migrations.RunPython(_forward, reverse_code=_reverse),
    ]
