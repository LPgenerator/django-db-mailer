"""Bootstrap the demo: create a superuser and sample dbmail data.

Replaces the legacy ``demo/auth.json`` fixture. Idempotent: running it
twice does not duplicate data.

Examples:

    python manage.py bootstrap_demo \\
        --username admin --email admin@example.com --password admin

The password may also be supplied via ``DJANGO_SUPERUSER_PASSWORD``.
"""

from __future__ import annotations

import os

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Create a demo superuser (replaces auth.json fixture)."

    def add_arguments(self, parser):
        parser.add_argument("--username", default="admin")
        parser.add_argument("--email", default="admin@example.com")
        parser.add_argument(
            "--password",
            default=os.environ.get("DJANGO_SUPERUSER_PASSWORD", "admin"),
        )

    def handle(self, *args, **options):
        User = get_user_model()
        username = options["username"]
        email = options["email"]
        password = options["password"]

        user, created = User.objects.get_or_create(
            username=username,
            defaults={"email": email, "is_staff": True, "is_superuser": True},
        )
        if created:
            user.set_password(password)
            user.save()
            self.stdout.write(self.style.SUCCESS(f"Created superuser: {username}"))
        else:
            self.stdout.write(f"Superuser {username} already exists, skipping.")
