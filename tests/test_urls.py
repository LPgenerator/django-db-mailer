"""Tests for `dbmail.urls` — namespaced reverse round-trips."""

from __future__ import annotations

import pytest
from django.urls import resolve, reverse

pytestmark = pytest.mark.django_db


@pytest.fixture
def admin_urlconf(settings):
    settings.ROOT_URLCONF = "tests.urls_admin"
    yield


class TestNamespacedRoutes:
    def test_db_mail_api_reverses(self, admin_urlconf):
        assert reverse("dbmail:db-mail-api") == "/dbmail/api/"

    def test_db_mail_tracker_reverses_with_arg(self, admin_urlconf):
        url = reverse("dbmail:db-mail-tracker", args=["abc"])
        assert url == "/dbmail/mail_read_tracker/abc/"

    def test_push_subscribe_reverses(self, admin_urlconf):
        url = reverse("dbmail:push-subscribe", kwargs={"reg_type": "web-push"})
        assert url == "/dbmail/web-push/subscribe/"

    def test_push_unsubscribe_reverses(self, admin_urlconf):
        url = reverse("dbmail:push-unsubscribe", kwargs={"reg_type": "mobile"})
        assert url == "/dbmail/mobile/unsubscribe/"

    def test_db_mail_api_resolves_to_view(self, admin_urlconf):
        match = resolve("/dbmail/api/")
        assert match.url_name == "db-mail-api"
        assert match.namespace == "dbmail"

    def test_tracker_resolves_with_path_param(self, admin_urlconf):
        match = resolve("/dbmail/mail_read_tracker/some-token/")
        assert match.url_name == "db-mail-tracker"
        assert "some-token" in match.args
