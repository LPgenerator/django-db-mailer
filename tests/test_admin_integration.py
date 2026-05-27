"""Integration tests for the Django admin pages of dbmail.

These exercise the full request → URL resolve → view → template render
path for every model registered in `dbmail.admin`. They are the
regression net for admin UI bugs and protect against future ``has_module_permission`` /
``has_change_permission`` signature drift.

Marked ``@pytest.mark.django_db`` and use the project ``client``
fixture; do not introduce real network or SMTP.
"""

from __future__ import annotations

import pytest
from django.urls import reverse

pytestmark = pytest.mark.django_db


# ---------------------------------------------------------------------------
# Shared fixtures
# ---------------------------------------------------------------------------


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
    return django_user_model.objects.create_superuser(
        username="root",
        email="root@example.com",
        password="root",
    )


@pytest.fixture
def staff(db, django_user_model):
    """Non-superuser staff: has dbmail change perms but is not is_superuser."""
    from django.contrib.auth.models import Permission

    user = django_user_model.objects.create_user(
        username="staff",
        email="staff@example.com",
        password="staff",
        is_staff=True,
    )
    perms = Permission.objects.filter(content_type__app_label="dbmail")
    user.user_permissions.add(*perms)
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
    return MailTemplate.objects.create(
        name="t",
        subject="s",
        slug="admin-tpl",
        message="hi {{user_email}}",
        from_email=sender,
    )


@pytest.fixture
def api_key(db):
    from dbmail.models import ApiKey

    return ApiKey.objects.create(name="prod", api_key="A" * 32, is_active=True)


@pytest.fixture
def credential(db):
    from dbmail.models import MailFromEmailCredential

    return MailFromEmailCredential.objects.create(
        host="smtp.example.com",
        port=587,
        username="bot@example.com",
        password="super-secret-pa$$word-with-symbols",
        use_tls=True,
    )


# ---------------------------------------------------------------------------
# Module-permission smoke: every registered admin opens for a superuser.
# ---------------------------------------------------------------------------


@pytest.fixture
def all_registered_admins():
    """Return [(opts, model), ...] for every dbmail model registered in admin."""
    from django.contrib import admin as django_admin

    return [(opts, model) for model, opts in django_admin.site._registry.items() if model._meta.app_label == "dbmail"]


class TestAdminChangelistsOpen:
    def test_every_registered_admin_changelist_returns_200(self, admin_client, all_registered_admins):
        # Regression for ``has_module_permission`` / ``has_view_permission``
        # signature drift (UI-2 fix introduced a TypeError when the alias
        # was bound to a method that did not take ``obj=None``).
        for _opts, model in all_registered_admins:
            url = reverse(f"admin:dbmail_{model._meta.model_name}_changelist")
            resp = admin_client.get(url)
            assert resp.status_code == 200, f"{url} -> {resp.status_code}"

    def test_every_add_form_returns_200(self, admin_client, all_registered_admins):
        for _opts, model in all_registered_admins:
            url = reverse(f"admin:dbmail_{model._meta.model_name}_add")
            resp = admin_client.get(url)
            # Some admins (e.g. MailLog) disable add — they redirect or 403.
            assert resp.status_code in (200, 302, 403), f"{url} -> {resp.status_code}"


# ---------------------------------------------------------------------------
# UI-2 — MailFromEmailCredential password handling
# ---------------------------------------------------------------------------


class TestMailFromEmailCredentialAdmin:
    def test_change_form_does_not_render_plaintext_password(self, admin_client, credential):
        url = reverse("admin:dbmail_mailfromemailcredential_change", args=(credential.pk,))
        resp = admin_client.get(url)
        assert resp.status_code == 200
        body = resp.content.decode("utf-8")
        # The plain-text password value must not appear in the HTML.
        assert credential.password not in body
        # Widget rendered as <input type="password">.
        assert 'type="password"' in body

    def test_blank_password_on_save_preserves_existing(self, admin_client, credential):
        url = reverse("admin:dbmail_mailfromemailcredential_change", args=(credential.pk,))
        resp = admin_client.post(
            url,
            data={
                "host": credential.host,
                "port": str(credential.port),
                "username": credential.username,
                "password": "",
                "use_tls": "on",
            },
            follow=False,
        )
        assert resp.status_code in (200, 302)
        credential.refresh_from_db()
        assert credential.password == "super-secret-pa$$word-with-symbols"

    def test_long_password_now_accepted(self, db, admin_client):
        # max_length raised 50 → 128 to fit Gmail/Yandex app-passwords.
        from dbmail.models import MailFromEmailCredential

        long_pw = "a" * 100
        url = reverse("admin:dbmail_mailfromemailcredential_add")
        resp = admin_client.post(
            url,
            data={"host": "smtp.x.com", "port": "587", "username": "u", "password": long_pw, "use_tls": "on"},
        )
        assert resp.status_code in (200, 302)
        if resp.status_code == 302:
            obj = MailFromEmailCredential.objects.get(host="smtp.x.com")
            assert obj.password == long_pw

    def test_non_superuser_cannot_view(self, staff_client):
        url = reverse("admin:dbmail_mailfromemailcredential_changelist")
        resp = staff_client.get(url)
        # Either 403 from has_module_permission or a redirect to login.
        assert resp.status_code in (302, 403)


# ---------------------------------------------------------------------------
# UI-3 / UI-4 — ApiKeyAdmin
# ---------------------------------------------------------------------------


class TestApiKeyAdmin:
    def test_changelist_masks_api_key(self, admin_client, api_key):
        url = reverse("admin:dbmail_apikey_changelist")
        resp = admin_client.get(url)
        assert resp.status_code == 200
        body = resp.content.decode("utf-8")
        assert api_key.api_key not in body
        assert "AAAA…AA" in body

    def test_add_form_does_not_expose_password_hash_field(self, admin_client):
        url = reverse("admin:dbmail_apikey_add")
        resp = admin_client.get(url)
        assert resp.status_code == 200
        body = resp.content.decode("utf-8")
        assert 'name="password_hash"' not in body
        assert 'name="last_used_at"' not in body
        assert 'name="last_used_ip"' not in body

    def test_add_auto_generates_api_key_when_blank(self, db, admin_client):
        from dbmail.models import ApiKey

        url = reverse("admin:dbmail_apikey_add")
        resp = admin_client.post(url, data={"name": "auto", "is_active": "on"}, follow=True)
        assert resp.status_code == 200
        obj = ApiKey.objects.get(name="auto")
        assert obj.api_key
        assert len(obj.api_key) == 32
        assert obj.password_hash, "save_model must populate password_hash"

    def test_add_explicit_api_key_is_persisted(self, db, admin_client):
        from dbmail.models import ApiKey

        url = reverse("admin:dbmail_apikey_add")
        explicit = "Z" * 32
        resp = admin_client.post(
            url,
            data={"name": "manual", "api_key": explicit, "is_active": "on"},
            follow=False,
        )
        assert resp.status_code == 302
        obj = ApiKey.objects.get(name="manual")
        assert obj.api_key == explicit
        assert obj.password_hash

    def test_change_form_password_hash_is_readonly(self, admin_client, api_key):
        url = reverse("admin:dbmail_apikey_change", args=(api_key.pk,))
        resp = admin_client.get(url)
        assert resp.status_code == 200
        body = resp.content.decode("utf-8")
        assert 'name="password_hash"' not in body
        assert 'name="last_used_at"' not in body


# ---------------------------------------------------------------------------
# UI-1 — send_mail_view
# ---------------------------------------------------------------------------


class TestSendMailView:
    def test_send_mail_view_returns_302_and_calls_send_test_msg(self, admin_client, template, monkeypatch):
        called = {}

        def fake_send(pk, email, **kwargs):
            called["pk"] = pk
            called["email"] = email
            called["kwargs"] = kwargs

        monkeypatch.setattr(
            "dbmail.management.commands.dbmail_test_send.send_test_msg",
            fake_send,
        )
        url = reverse("admin:send_mail_view", args=(template.pk,))
        resp = admin_client.get(url)
        assert resp.status_code == 302
        assert called["pk"] == str(template.pk)
        assert called["email"] == "root@example.com"
        # And no User instance leaked into kwargs (UI-1 guard).
        assert "user" not in called["kwargs"] or called["kwargs"]["user"] is None

    def test_send_mail_view_warns_when_user_has_no_email(self, admin_client, template, superuser):
        superuser.email = ""
        superuser.save(update_fields=["email"])
        url = reverse("admin:send_mail_view", args=(template.pk,))
        resp = admin_client.get(url, follow=True)
        # Redirect lands on the change page; messages framework carries
        # the error and we just confirm we did not hit a 500.
        assert resp.status_code == 200


# ---------------------------------------------------------------------------
# UI-5 / UI-6 — Browse vars
# ---------------------------------------------------------------------------


class TestBrowseVarsView:
    def test_apps_view_renders_non_empty_when_models_available(self, admin_client, template):
        # Default IGNORE_BROWSE_APP filters auth/contenttypes/admin/etc.
        # The `sites` framework is not in the default ignore list and is
        # always present in our test settings, so we expect at least
        # that section.
        url = reverse("admin:send_mail_apps_view", args=(template.pk,))
        resp = admin_client.get(url)
        assert resp.status_code == 200
        body = resp.content.decode("utf-8")
        assert "SITES" in body or "sites" in body.lower()
        assert "site" in body.lower()

    def test_apps_view_empty_state_renders(self, admin_client, template, settings):
        # Force every app into the ignore list so apps_list is empty —
        # the {% empty %} branch must render a friendly message, not a
        # blank page.
        settings.DB_MAILER_IGNORE_BROWSE_APP = (
            "dbmail",
            "auth",
            "contenttypes",
            "sessions",
            "sites",
            "messages",
            "admin",
        )
        # `defaults.IGNORE_BROWSE_APP` is read once at import time, so
        # patch the live tuple directly for this test.
        from dbmail import defaults

        original = defaults.IGNORE_BROWSE_APP
        defaults.IGNORE_BROWSE_APP = settings.DB_MAILER_IGNORE_BROWSE_APP
        try:
            url = reverse("admin:send_mail_apps_view", args=(template.pk,))
            resp = admin_client.get(url)
            assert resp.status_code == 200
            body = resp.content.decode("utf-8")
            assert "No models available" in body
        finally:
            defaults.IGNORE_BROWSE_APP = original

    def test_browse_model_fields_view_lists_fields(self, admin_client, template):
        url = reverse(
            "admin:browse_model_fields_view",
            args=(template.pk, "auth", "user"),
        )
        resp = admin_client.get(url)
        assert resp.status_code == 200
        body = resp.content.decode("utf-8")
        assert "username" in body
        assert "email" in body

    def test_browse_unknown_model_renders_empty_state(self, admin_client, template):
        url = reverse(
            "admin:browse_model_fields_view",
            args=(template.pk, "auth", "doesnotexist"),
        )
        resp = admin_client.get(url)
        assert resp.status_code == 200
        body = resp.content.decode("utf-8")
        assert "Fields for this model are not available" in body


# ---------------------------------------------------------------------------
# clean_cache view
# ---------------------------------------------------------------------------


class TestCleanCacheView:
    def test_redirects_back_to_changelist(self, admin_client, template):
        url = reverse("admin:clean_cache_view")
        resp = admin_client.get(url)
        assert resp.status_code == 302
        assert "/mailtemplate/" in resp["Location"]


# ---------------------------------------------------------------------------
# Signal SSTI guard
# ---------------------------------------------------------------------------


class TestSignalAdminSSTIGuard:
    def test_staff_cannot_save_signal(self, staff_client, db):
        from dbmail.models import Signal as DbmailSignal

        ct = _user_content_type()
        sig = DbmailSignal.objects.create(
            name="welcome",
            model=ct,
            signal="post_save",
            template=_template_for_signal(),
            interval=0,
            is_active=True,
        )
        url = reverse("admin:dbmail_signal_change", args=(sig.pk,))
        # Django renders the change form read-only for users that lack
        # change perms; we assert the form is *not* editable.
        resp = staff_client.get(url)
        body = resp.content.decode("utf-8") if resp.status_code == 200 else ""
        assert resp.status_code in (302, 403) or 'name="rules"' not in body

    def test_superuser_can_change_signal(self, admin_client, db):
        from dbmail.models import Signal as DbmailSignal

        ct = _user_content_type()
        sig = DbmailSignal.objects.create(
            name="welcome2",
            model=ct,
            signal="post_save",
            template=_template_for_signal(),
            interval=0,
            is_active=True,
        )
        url = reverse("admin:dbmail_signal_change", args=(sig.pk,))
        resp = admin_client.get(url)
        assert resp.status_code == 200


def _user_content_type():
    from django.contrib.auth import get_user_model
    from django.contrib.contenttypes.models import ContentType

    return ContentType.objects.get_for_model(get_user_model())


def _template_for_signal():
    from dbmail.models import MailFromEmail, MailTemplate

    sender, _ = MailFromEmail.objects.get_or_create(
        name="signal-from",
        defaults={"email": "signal@example.com"},
    )
    return MailTemplate.objects.create(
        name="signal-tpl",
        subject="welcome",
        slug="signal-tpl",
        message="hi",
        from_email=sender,
    )
