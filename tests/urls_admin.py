"""Test URL conf that wires admin and the namespaced dbmail include."""

from __future__ import annotations

from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("dbmail/", include("dbmail.urls", namespace="dbmail")),
]
