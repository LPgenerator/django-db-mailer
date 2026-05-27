from __future__ import annotations

import re

from django.core.management.base import BaseCommand

from dbmail import db_sender
from dbmail.defaults import BACKEND
from dbmail.models import MailTemplate


def send_test_msg(pk, email, user=None, **kwargs):
    template = MailTemplate.objects.get(pk=pk)
    slug = template.slug
    var_list = re.findall(r"\{\{\s?(\w+)\s?\}\}", template.message)
    context = {var: var.upper().replace("_", "-") for var in var_list}
    if user is None:
        return db_sender(slug, email, context, **kwargs)
    return db_sender(slug, email, user, context, **kwargs)


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument("--email", default="localhost", help="Recipients")
        parser.add_argument("--pk", default=1, help="DBMail template id")
        parser.add_argument(
            "--without-celery", action="store_true", default=False, dest="celery", help="Send direct message"
        )
        parser.add_argument("--provider", help="Provider")
        parser.add_argument("--backend", help="Backend")

    @staticmethod
    def get_kwargs(options):
        kwargs = {"use_celery": not options["celery"], "backend": BACKEND["mail"]}
        if options["provider"]:
            kwargs["provider"] = options["provider"]
        if options["backend"]:
            kwargs["backend"] = BACKEND[options["backend"]]
        return kwargs

    def handle(self, *args, **options):
        send_test_msg(options["pk"], options["email"], **self.get_kwargs(options))
        print("Done. Message was sent.")
