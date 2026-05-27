"""Global pytest fixtures for the dbmail test suite."""

from __future__ import annotations

import pytest


@pytest.fixture(autouse=True)
def _reset_cache():
    """Cache is per-test so rate-limit and api-key memo do not bleed."""
    from django.core.cache import cache

    cache.clear()
    yield
    cache.clear()


@pytest.fixture
def api_key(db):
    """Create an active ApiKey row with a known plain-text key."""
    from dbmail.models import ApiKey

    return ApiKey.objects.create(
        name="test",
        api_key="x" * 32,
        is_active=True,
    )


@pytest.fixture
def legacy_api_key(db):
    """ApiKey row that simulates a 2.x-style record (empty password_hash).

    Created via QuerySet.update() so the auto-hash branch in save() does
    not fire — we want the migration-style legacy state.
    """
    from dbmail.models import ApiKey

    obj = ApiKey.objects.create(name="legacy", api_key="y" * 32, is_active=True)
    ApiKey.objects.filter(pk=obj.pk).update(password_hash="")
    obj.refresh_from_db()
    return obj
