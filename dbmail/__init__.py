VERSION = (1, 1)


def get_version():
    return '.'.join(map(str, VERSION))


def send_db_mail(slug, recipient, *args, **kwargs):
    from dbmail.models import MailTemplate
    from dbmail.send_mail import SendMail
    from dbmail.defaults import CELERY_QUEUE

    args = (slug, recipient) + args
    try:
        import tasks

        tasks.send_db_mail.apply_async(
            args=args, kwargs=kwargs, queue=CELERY_QUEUE,
            priority=MailTemplate.get_template(slug=slug).priority
        )
    except ImportError:
        SendMail(*args, **kwargs).send()
