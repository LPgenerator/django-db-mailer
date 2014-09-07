import re
import optparse

from django.core.management.base import BaseCommand

from dbmail.models import MailTemplate
from dbmail import send_db_mail


def send_test_msg(pk, email, user=None):
    template = MailTemplate.objects.get(pk=pk)
    slug = template.slug
    var_list = re.findall('\{\{\s?(\w+)\s?\}\}', template.message)
    context = {}
    for var in var_list:
        context[var] = '"%s"' % var.upper().replace('_', '-')
    send_db_mail(slug, email, user, context)


class Command(BaseCommand):
    option_list = BaseCommand.option_list + (
        optparse.make_option('--email', dest='email', help='Recipients'),
        optparse.make_option('--pk', dest='pk', help='DBMail template id'),
    )

    def handle(self, *args, **options):
        send_test_msg(options['pk'], options['email'])
        print "Done. Message was sent."
