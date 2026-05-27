"""Regression tests for SEC-1 (provider RCE) and SEC-2 (SSTI).

SEC-1 — `dbmail/api/` previously accepted ``provider=arbitrary.module``
which the Sender backend fed into ``importlib.import_module``. With
the default settings the field is now stripped from the request kwargs
before reaching the backend.

SEC-2 — `MailTemplate.subject`/`message` and `MailBaseTemplate.message`
are rendered through Django's template engine. Non-superuser staff
must not be able to edit them.
"""

from __future__ import annotations

import pytest
from django.urls import reverse

pytestmark = pytest.mark.django_db


@pytest.fixture
def admin_urls(settings):
    settings.ROOT_URLCONF = "tests.urls_admin"
    settings.MIDDLEWARE = [
        "django.contrib.sessions.middleware.SessionMiddleware",
        "django.contrib.auth.middleware.AuthenticationMiddleware",
        "django.contrib.messages.middleware.MessageMiddleware",
    ]


@pytest.fixture
def superuser(db, django_user_model):
    return django_user_model.objects.create_superuser(username="root", email="root@example.com", password="root")


@pytest.fixture
def staff(db, django_user_model):
    from django.contrib.auth.models import Permission

    user = django_user_model.objects.create_user(
        username="staff", email="staff@example.com", password="staff", is_staff=True
    )
    user.user_permissions.add(*Permission.objects.filter(content_type__app_label="dbmail"))
    return user


@pytest.fixture
def admin_client(client, superuser, admin_urls):
    client.force_login(superuser)
    return client


@pytest.fixture
def staff_client(client, staff, admin_urls):
    client.force_login(staff)
    return client


@pytest.fixture
def template(db):
    from dbmail.models import MailFromEmail, MailTemplate

    sender = MailFromEmail.objects.create(name="from", email="from@example.com")
    return MailTemplate.objects.create(name="t", subject="hi", slug="t", message="hello", from_email=sender)


@pytest.fixture
def api_key(db):
    from dbmail.models import ApiKey

    return ApiKey.objects.create(name="prod", api_key="A" * 32, is_active=True)


# ---------------------------------------------------------------------------
# SEC-1 — provider RCE
# ---------------------------------------------------------------------------


class TestSec1ProviderOverride:
    @pytest.fixture
    def api_url(self, settings):
        settings.ROOT_URLCONF = "tests.urls_admin"
        return reverse("dbmail:db-mail-api")

    def test_provider_silently_dropped_by_default(self, client, api_key, template, api_url, settings):
        """Even with a valid api_key, an attacker-supplied ``provider=os``
        must not reach the dispatcher. The send still runs (whitelisted
        backend), but the provider field is filtered out before kwargs
        leave the view."""
        called = {}

        def fake_send(slug, recipient, *args, **kwargs):
            called["slug"] = slug
            called["recipient"] = recipient
            called["kwargs"] = kwargs

        from dbmail import views as v

        with pytest.MonkeyPatch().context() as mp:
            mp.setattr(v, "db_sender", fake_send)
            resp = client.post(
                api_url,
                data={
                    "api_key": api_key.api_key,
                    "slug": template.slug,
                    "recipient": "user@example.com",
                    "provider": "os",  # attacker payload
                },
            )
        # Send goes through (200 OK), but provider must have been
        # filtered before db_sender saw it.
        assert resp.status_code == 200
        assert "provider" not in called["kwargs"]

    def test_provider_override_requires_explicit_setting(self, client, api_key, template, api_url, settings):
        """With opt-in flag but no allowlist, provider is rejected with
        403 Forbidden."""
        settings.DB_MAILER_API_ALLOW_PROVIDER_OVERRIDE = True
        settings.DB_MAILER_API_PROVIDER_ALLOWLIST = ()
        resp = client.post(
            api_url,
            data={
                "api_key": api_key.api_key,
                "slug": template.slug,
                "recipient": "u@e.com",
                "provider": "dbmail.providers.iqsms.sms",
            },
        )
        assert resp.status_code == 403

    def test_provider_override_in_allowlist_passes(self, client, api_key, template, api_url, settings):
        """Opt-in flag + allowlist match → request reaches db_sender."""
        settings.DB_MAILER_API_ALLOW_PROVIDER_OVERRIDE = True
        settings.DB_MAILER_API_PROVIDER_ALLOWLIST = ("dbmail.providers.iqsms.sms",)
        called = {}

        def fake_send(slug, recipient, *args, **kwargs):
            called["kwargs"] = kwargs

        from dbmail import views as v

        with pytest.MonkeyPatch().context() as mp:
            mp.setattr(v, "db_sender", fake_send)
            resp = client.post(
                api_url,
                data={
                    "api_key": api_key.api_key,
                    "slug": template.slug,
                    "recipient": "u@e.com",
                    "provider": "dbmail.providers.iqsms.sms",
                },
            )
        assert resp.status_code == 200
        assert called["kwargs"].get("provider") == "dbmail.providers.iqsms.sms"

    def test_api_disable_kill_switch(self, client, api_key, template, api_url, settings):
        settings.DB_MAILER_API_DISABLE = True
        resp = client.post(
            api_url,
            data={
                "api_key": api_key.api_key,
                "slug": template.slug,
                "recipient": "u@e.com",
            },
        )
        assert resp.status_code == 403


# ---------------------------------------------------------------------------
# SEC-2 — MailTemplate / MailBaseTemplate / Signal SSTI guard
# ---------------------------------------------------------------------------


class TestSec2MailTemplateGuard:
    def test_staff_change_form_renders_subject_and_message_readonly(self, staff_client, template):
        url = reverse("admin:dbmail_mailtemplate_change", args=(template.pk,))
        resp = staff_client.get(url)
        assert resp.status_code == 200
        body = resp.content.decode("utf-8")
        # Editable inputs would carry name="subject" / name="message".
        # When the field is in get_readonly_fields, Django renders a
        # static representation instead.
        assert 'name="subject"' not in body
        assert 'name="message"' not in body

    def test_staff_cannot_add_template(self, staff_client):
        url = reverse("admin:dbmail_mailtemplate_add")
        resp = staff_client.get(url)
        # Forbidden / redirect to admin index; importantly not 200 with
        # an editable form.
        assert resp.status_code in (302, 403)

    def test_superuser_change_form_keeps_fields_editable(self, admin_client, template):
        url = reverse("admin:dbmail_mailtemplate_change", args=(template.pk,))
        resp = admin_client.get(url)
        assert resp.status_code == 200
        body = resp.content.decode("utf-8")
        assert 'name="subject"' in body
        assert 'name="message"' in body


class TestSec2MailBaseTemplateGuard:
    def test_staff_cannot_add_base_template(self, staff_client):
        url = reverse("admin:dbmail_mailbasetemplate_add")
        resp = staff_client.get(url)
        assert resp.status_code in (302, 403)

    def test_superuser_can_add_base_template(self, admin_client):
        url = reverse("admin:dbmail_mailbasetemplate_add")
        resp = admin_client.get(url)
        assert resp.status_code == 200
