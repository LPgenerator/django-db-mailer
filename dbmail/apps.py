from __future__ import annotations

from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class DBMailConfig(AppConfig):
    name = "dbmail"
    verbose_name = _("DB Mailer")
    default_auto_field = "django.db.models.BigAutoField"

    def ready(self) -> None:
        from dbmail import initial_signals
        from dbmail.defaults import ALLOWED_MODELS_ON_ADMIN

        if "Signal" in ALLOWED_MODELS_ON_ADMIN:
            initial_signals()
