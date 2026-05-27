"""Tests for the demo project (phase 06)."""

from __future__ import annotations

import pytest


@pytest.fixture
def _add_demo_to_path():
    """Make ``demo.*`` importable for tests in this module.

    The default ``tests/settings.py`` does not include the demo project
    on PYTHONPATH because most tests target the dbmail package itself.
    """
    import os
    import sys

    demo_root = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "demo",
    )
    if demo_root not in sys.path:
        sys.path.insert(0, demo_root)
    yield
    if demo_root in sys.path:
        sys.path.remove(demo_root)


class TestDemoSettingsLoad:
    def test_demo_settings_module_is_importable(self, _add_demo_to_path):
        # Importing demo.settings must not raise even when DJANGO_DEBUG
        # is unset and optional admin extensions may be missing.
        import importlib

        # Use a fresh import to avoid state pollution across tests.
        if "demo.settings" in importlib.sys.modules:
            del importlib.sys.modules["demo.settings"]
        importlib.import_module("demo.settings")


class TestBootstrapDemoCommand:
    """The ``bootstrap_demo`` command must be idempotent."""

    def test_bootstrap_demo_module_imports(self, _add_demo_to_path):
        import importlib

        importlib.import_module("demo.management.commands.bootstrap_demo")

    @pytest.mark.django_db
    def test_bootstrap_demo_idempotency_at_unit_level(self, _add_demo_to_path):
        # Exercise just the handle() logic against the default User
        # model so we don't need to switch DJANGO_SETTINGS_MODULE for
        # the whole pytest run.
        import io

        from demo.management.commands.bootstrap_demo import Command
        from django.contrib.auth import get_user_model

        User = get_user_model()
        User.objects.filter(username="admin").delete()

        cmd = Command()
        cmd.stdout = io.StringIO()
        cmd.handle(username="admin", email="a@example.com", password="p")
        assert User.objects.filter(username="admin", is_superuser=True).count() == 1

        out = cmd.stdout.getvalue()
        cmd.handle(username="admin", email="a@example.com", password="p")
        assert User.objects.filter(username="admin").count() == 1
        # The last stdout chunk reports "already exists".
        assert "already exists" in cmd.stdout.getvalue()[len(out) :]


@pytest.mark.django_db
class TestBootstrapDemoCommandDB:
    def test_bootstrap_demo_creates_superuser(self, _add_demo_to_path):
        from demo.management.commands.bootstrap_demo import Command
        from django.contrib.auth import get_user_model

        User = get_user_model()
        User.objects.filter(username="admin").delete()
        cmd = Command()
        import io

        cmd.stdout = io.StringIO()
        cmd.handle(username="admin", email="a@example.com", password="secret")
        user = User.objects.get(username="admin")
        assert user.is_superuser
        assert user.is_staff
        assert user.email == "a@example.com"
