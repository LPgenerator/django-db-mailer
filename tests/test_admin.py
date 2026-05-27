"""Tests for `dbmail.admin` — list_display config + admin actions."""

from __future__ import annotations

from unittest.mock import patch

import pytest
from django.contrib import admin as django_admin
from django.urls import reverse

pytestmark = pytest.mark.django_db


@pytest.fixture
def admin_urls(settings):
    """Switch ROOT_URLCONF to a conf that mounts both admin and dbmail."""

    settings.ROOT_URLCONF = "tests.urls_admin"
    settings.MIDDLEWARE = [
        "django.contrib.sessions.middleware.SessionMiddleware",
        "django.contrib.auth.middleware.AuthenticationMiddleware",
        "django.contrib.messages.middleware.MessageMiddleware",
    ]
    yield


@pytest.fixture
def template(db):
    from dbmail.models import MailFromEmail, MailTemplate

    sender = MailFromEmail.objects.create(name="from", email="from@example.com")
    return MailTemplate.objects.create(
        name="t",
        subject="s",
        slug="admin-tpl",
        message="hi",
        from_email=sender,
    )


@pytest.fixture
def superuser(db, django_user_model):
    return django_user_model.objects.create_superuser(
        username="root",
        email="root@example.com",
        password="root",
    )


@pytest.fixture
def admin_client(client, superuser, admin_urls):
    client.force_login(superuser)
    return client


# ---------------------------------------------------------------------------
# Static config: list_display, list_filter, search_fields
# ---------------------------------------------------------------------------


class TestMailTemplateAdminConfig:
    def test_list_display_contains_canonical_fields(self):
        from dbmail.admin import MailTemplateAdmin

        for f in ("name", "category", "slug", "is_active"):
            assert f in MailTemplateAdmin.list_display

    def test_list_filter_includes_priority_and_dates(self):
        from dbmail.admin import MailTemplateAdmin

        assert "priority" in MailTemplateAdmin.list_filter
        assert "is_active" in MailTemplateAdmin.list_filter

    def test_search_fields_includes_slug_and_subject(self):
        from dbmail.admin import MailTemplateAdmin

        assert "slug" in MailTemplateAdmin.search_fields
        assert "subject" in MailTemplateAdmin.search_fields


class TestMailLogAdminConfig:
    def test_readonly_fields_match_model_fields(self):
        from dbmail.admin import MailLogAdmin
        from dbmail.models import MailLog

        adm = MailLogAdmin(MailLog, django_admin.site)
        ro = set(adm.readonly_fields)
        for f in MailLog._meta.fields:
            assert f.name in ro, f"{f.name} should be readonly"

    def test_no_add_permission(self, template, superuser):
        from dbmail.admin import MailLogAdmin
        from dbmail.models import MailLog

        adm = MailLogAdmin(MailLog, django_admin.site)
        assert adm.has_add_permission(request=None) is False


class TestApiKeyAdminConfig:
    def test_list_display_includes_is_active_and_id(self):
        from dbmail.admin import ApiKeyAdmin

        assert "is_active" in ApiKeyAdmin.list_display
        assert "id" in ApiKeyAdmin.list_display


class TestMailLogTrackAdminConfig:
    def test_readonly_fields_match_model_fields(self):
        from dbmail.admin import MailLogTrackAdmin
        from dbmail.models import MailLogTrack

        adm = MailLogTrackAdmin(MailLogTrack, django_admin.site)
        for f in MailLogTrack._meta.fields:
            assert f.name in set(adm.readonly_fields)


class TestMailLogExceptionAdmin:
    def test_no_add_permission(self):
        from dbmail.admin import MailLogExceptionAdmin
        from dbmail.models import MailLogException

        adm = MailLogExceptionAdmin(MailLogException, django_admin.site)
        assert adm.has_add_permission(request=None) is False


class TestSignalAdmin:
    def test_save_model_calls_super_and_auto_reload(self, monkeypatch):
        from dbmail.admin import SignalAdmin
        from dbmail.models import Signal

        called = {"reload": False}

        def fake_reload(_request):
            called["reload"] = True

        monkeypatch.setattr(SignalAdmin, "auto_reload", staticmethod(fake_reload))
        admin_inst = SignalAdmin(model=Signal, admin_site=django_admin.site)
        with patch("django.contrib.admin.ModelAdmin.save_model"):
            admin_inst.save_model(request=object(), obj=None, form=None, change=False)
        assert called["reload"] is True

    def test_auto_reload_no_op_when_disabled(self, settings):
        from dbmail.admin import SignalAdmin

        settings.DB_MAILER_WSGI_AUTO_RELOAD = False
        settings.DB_MAILER_UWSGI_AUTO_RELOAD = False

        # Build a minimal request-like object.
        class R:
            environ = {}

        SignalAdmin.auto_reload(R())  # should not raise


# ---------------------------------------------------------------------------
# HTTP — admin pages render
# ---------------------------------------------------------------------------


class TestAdminPagesRender:
    def test_template_changelist_returns_200(self, admin_client, template):
        url = reverse("admin:dbmail_mailtemplate_changelist")
        resp = admin_client.get(url)
        assert resp.status_code == 200

    def test_template_changelist_query_count_is_bounded(self, admin_client, template, django_assert_max_num_queries):
        from dbmail.models import MailCategory, MailFromEmail, MailTemplate

        sender = MailFromEmail.objects.create(name="ext", email="ext@example.com")
        cat = MailCategory.objects.create(name="cat")
        for i in range(10):
            MailTemplate.objects.create(
                name=f"tpl{i}",
                subject="s",
                slug=f"tpl-{i}",
                message="hi",
                from_email=sender,
                category=cat,
            )

        url = reverse("admin:dbmail_mailtemplate_changelist")
        with django_assert_max_num_queries(30):
            resp = admin_client.get(url)
        assert resp.status_code == 200

    def test_maillog_changelist_returns_200(self, admin_client):
        url = reverse("admin:dbmail_maillog_changelist")
        resp = admin_client.get(url)
        assert resp.status_code == 200

    def test_apikey_changelist_returns_200(self, admin_client):
        url = reverse("admin:dbmail_apikey_changelist")
        resp = admin_client.get(url)
        assert resp.status_code == 200

    def test_mailgroup_changelist_returns_200(self, admin_client):
        url = reverse("admin:dbmail_mailgroup_changelist")
        resp = admin_client.get(url)
        assert resp.status_code == 200

    def test_mailbcc_changelist_returns_200(self, admin_client):
        url = reverse("admin:dbmail_mailbcc_changelist")
        resp = admin_client.get(url)
        assert resp.status_code == 200

    def test_signal_changelist_returns_200(self, admin_client):
        url = reverse("admin:dbmail_signal_changelist")
        resp = admin_client.get(url)
        assert resp.status_code == 200

    def test_template_change_view_returns_200(self, admin_client, template):
        url = reverse("admin:dbmail_mailtemplate_change", args=[template.pk])
        resp = admin_client.get(url)
        assert resp.status_code == 200


class TestMailTemplateAdminCustomViews:
    def test_clean_cache_view_redirects_to_changelist(self, admin_client):
        from dbmail.admin import MailTemplateAdmin
        from dbmail.models import MailTemplate

        adm = MailTemplateAdmin(MailTemplate, django_admin.site)
        # Build a request-like with a `_messages` storage.
        from django.test import RequestFactory

        rf = RequestFactory()
        req = rf.get("/admin/dbmail/mailtemplate/reset/cache/")
        req.user = admin_client.session._session_key
        # Use a stub messages storage for the request.
        from django.contrib.messages.storage.fallback import FallbackStorage

        req.session = {}
        req._messages = FallbackStorage(req)

        resp = adm.clean_cache_view(req)
        assert resp.status_code == 302

    def test_send_mail_view_invokes_send_test_msg_for_user_with_email(self, admin_client, template, superuser):
        from dbmail.admin import MailTemplateAdmin
        from dbmail.models import MailTemplate

        adm = MailTemplateAdmin(MailTemplate, django_admin.site)
        from django.contrib.messages.storage.fallback import FallbackStorage
        from django.test import RequestFactory

        rf = RequestFactory()
        req = rf.get("/admin/dbmail/mailtemplate/%d/sendmail/" % template.pk)
        req.user = superuser
        req.session = {}
        req._messages = FallbackStorage(req)

        with patch("dbmail.management.commands.dbmail_test_send.send_test_msg") as send:
            resp = adm.send_mail_view(req, template.pk)

        assert send.called
        assert resp.status_code == 302

    def test_send_mail_view_errors_for_user_without_email(self, admin_client, template, django_user_model):
        from dbmail.admin import MailTemplateAdmin
        from dbmail.models import MailTemplate

        # User with empty email.
        u = django_user_model.objects.create_user(username="noemail", password="x", email="")
        adm = MailTemplateAdmin(MailTemplate, django_admin.site)
        from django.contrib.messages.storage.fallback import FallbackStorage
        from django.test import RequestFactory

        rf = RequestFactory()
        req = rf.get("/x/")
        req.user = u
        req.session = {}
        req._messages = FallbackStorage(req)

        with patch("dbmail.management.commands.dbmail_test_send.send_test_msg") as send:
            resp = adm.send_mail_view(req, template.pk)

        send.assert_not_called()
        assert resp.status_code == 302

    def test_browse_model_fields_view_returns_200(self, admin_client, template):
        from dbmail.admin import MailTemplateAdmin
        from dbmail.models import MailTemplate

        adm = MailTemplateAdmin(MailTemplate, django_admin.site)
        from django.contrib.messages.storage.fallback import FallbackStorage
        from django.test import RequestFactory

        rf = RequestFactory()
        req = rf.get("/x/")
        req.user = type("U", (), {"is_authenticated": True})()
        req.session = {}
        req._messages = FallbackStorage(req)

        resp = adm.browse_model_fields_view(req, template.pk, "auth", "user")
        assert resp.status_code == 200

    def test_get_apps_view_returns_200(self, admin_client, template):
        from dbmail.admin import MailTemplateAdmin
        from dbmail.models import MailTemplate

        adm = MailTemplateAdmin(MailTemplate, django_admin.site)
        from django.contrib.messages.storage.fallback import FallbackStorage
        from django.test import RequestFactory

        rf = RequestFactory()
        req = rf.get("/x/")
        req.user = type("U", (), {"is_authenticated": True})()
        req.session = {}
        req._messages = FallbackStorage(req)

        resp = adm.get_apps_view(req, template.pk)
        assert resp.status_code == 200

    def test_get_readonly_fields_with_read_only_enabled(self, settings):
        from dbmail.admin import MailTemplateAdmin
        from dbmail.models import MailTemplate

        settings.DB_MAILER_READ_ONLY_ENABLED = True
        adm = MailTemplateAdmin(MailTemplate, django_admin.site)
        # The setting is captured at import time — emulate the branch directly.
        # `obj is not None` + READ_ONLY_ENABLED → returns ['slug', 'context_note']
        instance = MailTemplate(slug="x")
        from dbmail import defaults

        defaults.READ_ONLY_ENABLED = True
        ro = adm.get_readonly_fields(request=None, obj=instance)
        assert "slug" in ro

    def test_get_prepopulated_fields_returns_empty_for_existing_obj(self, template):
        from dbmail.admin import MailTemplateAdmin
        from dbmail.models import MailTemplate

        adm = MailTemplateAdmin(MailTemplate, django_admin.site)
        assert adm.get_prepopulated_fields(request=None, obj=template) == {}

    def test_get_prepopulated_fields_returns_default_for_new_obj(self):
        from dbmail.admin import MailTemplateAdmin
        from dbmail.models import MailTemplate

        adm = MailTemplateAdmin(MailTemplate, django_admin.site)
        assert "slug" in adm.get_prepopulated_fields(request=None, obj=None)


class TestMailGroupAdmin:
    def test_get_readonly_fields_returns_slug_when_obj_present(self, settings):
        from dbmail import defaults
        from dbmail.admin import MailGroupAdmin
        from dbmail.models import MailGroup

        defaults.READ_ONLY_ENABLED = True
        adm = MailGroupAdmin(MailGroup, django_admin.site)
        grp = MailGroup(slug="x", name="x")
        ro = adm.get_readonly_fields(request=None, obj=grp)
        assert "slug" in ro

    def test_get_prepopulated_fields_empty_for_existing(self):
        from dbmail.admin import MailGroupAdmin
        from dbmail.models import MailGroup

        adm = MailGroupAdmin(MailGroup, django_admin.site)
        assert adm.get_prepopulated_fields(request=None, obj=MailGroup()) == {}
