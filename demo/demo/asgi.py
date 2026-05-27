"""ASGI entrypoint for the django-db-mailer demo project."""

from __future__ import annotations

import os

from django.core.asgi import get_asgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "demo.settings")

application = get_asgi_application()
