"""End-to-end Signal pipeline regression tests.

Owner asked: "do we have tests that, when a Signal-row triggers a
post_save on User, we actually send an email?". This file is the
answer — full pipeline, no mocks of the dispatcher path:

    Signal row + post_save signal connect → SignalReceiver.run()
    → Sender → EmailMessage → ``django.core.mail.outbox``.

Sibling tests cover the inactive / receive_once / interval branches
(deferred-signal queue path).
"""

from __future__ import annotations

import pytest

pytestmark = pytest.mark.django_db


@pytest.fixture
def locmem_email(settings):
    settings.EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"


@pytest.fixture
def signal_template(db):
    from dbmail.models import MailFromEmail, MailTemplate

    sender = MailFromEmail.objects.create(name="signal-from", email="signal@example.com")
    return MailTemplate.objects.create(
        name="user-welcome",
        subject="Welcome {{instance.username}}",
        slug="user-welcome",
        message="Hello {{instance.username}}, your email is {{instance.email}}.",
        is_html=False,
        from_email=sender,
    )


@pytest.fixture
def post_save_user_signal(db, signal_template):
    """Create a Signal row + connect listeners (mimics apps.ready)."""
    from django.contrib.auth import get_user_model
    from django.contrib.contenttypes.models import ContentType

    from dbmail.models import Signal as DbmailSignal
    from dbmail.signals import initial_signals

    User = get_user_model()
    ct = ContentType.objects.get_for_model(User)
    sig = DbmailSignal.objects.create(
        name="user-welcome-signal",
        model=ct,
        signal="post_save",
        template=signal_template,
        interval=0,
        is_active=True,
    )
    initial_signals()
    yield sig
    # Disconnect to avoid leaking into other tests.
    from django.db.models.signals import post_save

    post_save.disconnect(dispatch_uid=f"dbmail-signal-{sig.pk}")


class TestSignalPipelineE2E:
    def test_post_save_user_sends_email(self, post_save_user_signal, locmem_email, django_user_model):
        from django.core import mail

        mail.outbox.clear()
        django_user_model.objects.create_user(username="alice", email="alice@example.com", password="x")
        assert len(mail.outbox) == 1
        msg = mail.outbox[0]
        assert msg.subject == "Welcome alice"
        assert "alice@example.com" in msg.body
        assert msg.to == ["alice@example.com"]

    def test_inactive_signal_does_not_send(self, post_save_user_signal, locmem_email, django_user_model):
        from django.core import mail

        post_save_user_signal.is_active = False
        post_save_user_signal.save()
        # Reconnect listeners — initial_signals() filters by is_active.
        from dbmail.signals import initial_signals

        initial_signals()
        mail.outbox.clear()
        django_user_model.objects.create_user(username="bob", email="bob@example.com", password="x")
        assert len(mail.outbox) == 0

    def test_celery_dispatch_path_does_not_leak_user_instance(
        self, post_save_user_signal, locmem_email, django_user_model, settings
    ):
        # Plan3 UI-1 guarded ``send_test_msg``; the same risk exists on
        # the Celery dispatcher when Signal rows fire post_save under a
        # real broker that uses the JSON serializer. With
        # CELERY_TASK_ALWAYS_EAGER the path is exercised end-to-end and
        # the task body must not blow up trying to JSON-serialize a
        # User instance.
        settings.CELERY_TASK_ALWAYS_EAGER = True
        settings.CELERY_TASK_EAGER_PROPAGATES = True
        from django.core import mail

        mail.outbox.clear()
        django_user_model.objects.create_user(username="carol", email="carol@example.com", password="x")
        # If Celery had failed to serialize, the eager-propagate would
        # have raised inside create_user; reaching this line proves the
        # path is JSON-clean.
        assert len(mail.outbox) == 1


class TestApiKeyAutoHash:
    """Owner-visible side-effect: ApiKey.objects.create populates hash."""

    def test_create_populates_password_hash(self, db):
        from dbmail.models import ApiKey

        key = ApiKey.objects.create(name="auto", api_key="X" * 32)
        assert key.password_hash
        assert key.password_hash.startswith(("pbkdf2_sha256$", "argon2$"))

    def test_is_valid_key_round_trip(self, db):
        from dbmail.models import ApiKey

        key = ApiKey.objects.create(name="rt", api_key="Y" * 32)
        assert key.is_valid_key("Y" * 32)
        assert not key.is_valid_key("Z" * 32)
