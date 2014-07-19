VERSION = (1, 1)


def get_version():
    return '.'.join(map(str, VERSION))


def send_db_mail(slug, recipient, *args, **kwargs):
    from dbmail.defaults import CELERY_QUEUE
    from dbmail.models import MailTemplate
    from dbmail.send_mail import SendMail
    from django.conf import settings

    args = (slug, recipient) + args
    try:
        import tasks

        if 'djcelery' not in settings.INSTALLED_APPS:
            raise ImportError

        tasks.send_db_mail.apply_async(
            args=args, kwargs=kwargs, queue=CELERY_QUEUE,
            priority=MailTemplate.get_template(slug=slug).priority
        )
    except ImportError:
        SendMail(*args, **kwargs).send()
