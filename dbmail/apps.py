# -*- encoding: utf-8 -*-

from django.utils.translation import ugettext_lazy as _
from django.apps import AppConfig


class DBMailConfig(AppConfig):
    name = 'dbmail'
    verbose_name = _('DB Mailer')

    def ready(self):
        from dbmail import initial_signals

        initial_signals()
