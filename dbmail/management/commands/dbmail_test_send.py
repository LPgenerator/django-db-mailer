import re
import optparse

from django.core.management.base import BaseCommand

from dbmail.models import MailTemplate
from dbmail.defaults import BACKEND
from dbmail import db_sender


def send_test_msg(pk, email, user=None, **kwargs):
    template = MailTemplate.objects.get(pk=pk)
    slug = template.slug
    var_list = re.findall('\{\{\s?(\w+)\s?\}\}', template.message)
    context = {}
    for var in var_list:
        context[var] = '%s' % var.upper().replace('_', '-')
    return db_sender(slug, email, user, context, **kwargs)


class Command(BaseCommand):
    option_list = BaseCommand.option_list + (
        optparse.make_option('--email', dest='email', help='Recipients'),
        optparse.make_option('--pk', dest='pk', help='DBMail template id'),
        optparse.make_option('--without-celery', action='store_true',
                             default=False, dest='celery',
                             help='Send direct message'),
        optparse.make_option('--provider', dest='provider', help='Provider'),
        optparse.make_option(
            '--backend', dest='backend', help='Backend', default='mail'),
    )

    @staticmethod
    def get_kwargs(options):
        kwargs = {
            'use_celery': not options['celery'],
            'backend': BACKEND['mail']}
        if options['provider']:
            kwargs['provider'] = options['provider']
        if options['backend']:
            kwargs['backend'] = BACKEND[options['backend']]
        return kwargs

    def handle(self, *args, **options):
        send_test_msg(
            options['pk'], options['email'], **self.get_kwargs(options)
        )
        print("Done. Message was sent.")
