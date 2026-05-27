from __future__ import annotations

from django.apps import AppConfig


class DemoConfig(AppConfig):
    name = "demo"
    label = "demo"
    verbose_name = "django-db-mailer demo"
    default_auto_field = "django.db.models.BigAutoField"
