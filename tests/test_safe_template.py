"""Tests for the opt-in Jinja2 sandbox renderer (security audit item M-1)."""

from __future__ import annotations

import builtins
from unittest import mock

import pytest

from dbmail.safe_template import _JINJA2_INSTALL_HINT, SandboxedRenderer

# ---------------------------------------------------------------------------
# Unit tests — SandboxedRenderer in isolation.
# ---------------------------------------------------------------------------


def test_sandboxed_renderer_renders_simple_template():
    renderer = SandboxedRenderer()
    assert renderer.render("Hello {{ name }}!", {"name": "Alice"}) == "Hello Alice!"


def test_sandboxed_renderer_blocks_class_access():
    """`{{ x.__class__ }}` is the entrypoint of every SSTI chain.

    Jinja2's SandboxedEnvironment marks the attribute as unsafe; rendering
    a leaf access produces ``Undefined`` (empty string in autoescape mode)
    rather than the class repr.  The class object itself never reaches the
    output.
    """
    renderer = SandboxedRenderer()
    out = renderer.render("{{ user.__class__ }}", {"user": object()})
    assert "<class" not in out
    assert "object" not in out
    assert out == ""


def test_sandboxed_renderer_blocks_globals_walk():
    """The full SSTI chain — __init__.__globals__ — is blocked."""
    from jinja2.exceptions import SecurityError

    renderer = SandboxedRenderer()
    with pytest.raises(SecurityError):
        renderer.render("{{ user.__init__.__globals__ }}", {"user": object()})


def test_sandboxed_renderer_autoescape_on():
    renderer = SandboxedRenderer()
    out = renderer.render("{{ html }}", {"html": "<script>alert(1)</script>"})
    assert "<script>" not in out
    assert "&lt;script&gt;" in out


def test_sandboxed_renderer_raises_import_error_when_jinja2_missing():
    """If jinja2 is uninstalled, instantiation fails with a helpful hint."""
    real_import = builtins.__import__

    def fake_import(name, *args, **kwargs):
        if name.startswith("jinja2"):
            raise ImportError("No module named 'jinja2'")
        return real_import(name, *args, **kwargs)

    with mock.patch.object(builtins, "__import__", side_effect=fake_import):
        with pytest.raises(ImportError) as exc:
            SandboxedRenderer()
    assert "pip install" in str(exc.value)
    assert _JINJA2_INSTALL_HINT == str(exc.value)


# ---------------------------------------------------------------------------
# Integration tests — Sender._render_template branching on the setting.
# ---------------------------------------------------------------------------


pytestmark_db = pytest.mark.django_db


@pytest.fixture
def template(db):
    from dbmail.models import MailFromEmail, MailTemplate

    sender_addr = MailFromEmail.objects.create(name="S", email="s@example.com")
    return MailTemplate.objects.create(
        name="T",
        subject="Hello {{ name }}",
        from_email=sender_addr,
        message="Hi {{ name }}",
        slug="safe-tpl",
        is_html=False,
        is_active=True,
    )


@pytest.mark.django_db
def test_mail_render_uses_django_template_by_default(template):
    """Default behaviour is unchanged — Django's template engine is used."""
    from dbmail.backends.mail import Sender

    sender = Sender("safe-tpl", "to@example.com", {"name": "Bob"}, backend="mail")
    assert sender._subject == "Hello Bob"
    assert sender._message == "Hi Bob"


@pytest.mark.django_db
def test_mail_render_uses_sandbox_when_enabled(template, settings):
    """Flipping the setting routes rendering through the Jinja2 sandbox."""
    settings.DB_MAILER_USE_JINJA2_SANDBOX = True
    # `dbmail.defaults` was imported at startup with the flag = False; reload
    # it so the module-level constant picks up the override.
    import importlib

    from dbmail import defaults as defaults_module

    importlib.reload(defaults_module)
    try:
        from dbmail.backends import mail as mail_module

        importlib.reload(mail_module)
        sender = mail_module.Sender("safe-tpl", "to@example.com", {"name": "Bob"}, backend="mail")
        assert sender._subject == "Hello Bob"
        assert sender._message == "Hi Bob"
    finally:
        # Restore the import-time defaults so later tests see the original
        # USE_JINJA2_SANDBOX = False.
        settings.DB_MAILER_USE_JINJA2_SANDBOX = False
        importlib.reload(defaults_module)
        from dbmail.backends import mail as mail_module

        importlib.reload(mail_module)


@pytest.mark.django_db
def test_mail_render_sandbox_blocks_ssti(db, settings):
    """A malicious template body cannot reach Django settings via the sandbox."""
    from jinja2.exceptions import SecurityError

    from dbmail.models import MailFromEmail, MailTemplate

    sender_addr = MailFromEmail.objects.create(name="S", email="s@example.com")
    MailTemplate.objects.create(
        name="evil",
        subject="hi",
        from_email=sender_addr,
        message="{{ user.__class__.__init__.__globals__ }}",
        slug="evil-tpl",
        is_html=False,
        is_active=True,
    )

    settings.DB_MAILER_USE_JINJA2_SANDBOX = True
    import importlib

    from dbmail import defaults as defaults_module

    importlib.reload(defaults_module)
    try:
        from dbmail.backends import mail as mail_module

        importlib.reload(mail_module)
        with pytest.raises(SecurityError):
            mail_module.Sender("evil-tpl", "to@example.com", {"user": object()}, backend="mail")
    finally:
        settings.DB_MAILER_USE_JINJA2_SANDBOX = False
        importlib.reload(defaults_module)
        from dbmail.backends import mail as mail_module

        importlib.reload(mail_module)
