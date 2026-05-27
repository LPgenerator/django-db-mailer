"""Data migration: populate ``ApiKey.password_hash`` from ``ApiKey.api_key``.

For a fresh ``3.0`` installation this migration is a no-op (no existing
``ApiKey`` rows). For installations upgrading from ``2.x`` via the
``--fake-initial`` route described in MIGRATION.md, this migration
hashes the legacy plain-text ``api_key`` values into ``password_hash``
on first ``manage.py migrate`` after upgrade. See ADR-0006 / ADR-0009.

Reverse clears ``password_hash`` (the legacy plain ``api_key`` column
remains the source of truth for reverse).
"""

from __future__ import annotations

from django.db import migrations


def _hash_existing_keys(apps, schema_editor):
    from django.contrib.auth.hashers import make_password

    ApiKey = apps.get_model("dbmail", "ApiKey")
    db_alias = schema_editor.connection.alias
    queryset = ApiKey.objects.using(db_alias).filter(password_hash="")
    for row in queryset.iterator():
        if not row.api_key:
            continue
        ApiKey.objects.using(db_alias).filter(pk=row.pk).update(
            password_hash=make_password(row.api_key),
        )


def _clear_hashes(apps, schema_editor):
    ApiKey = apps.get_model("dbmail", "ApiKey")
    db_alias = schema_editor.connection.alias
    ApiKey.objects.using(db_alias).update(password_hash="")


class Migration(migrations.Migration):
    dependencies = [
        ("dbmail", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(_hash_existing_keys, reverse_code=_clear_hashes),
    ]
