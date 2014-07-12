VERSION = (1, 0)


def get_version():
    return '.'.join(map(str, VERSION))


def send_db_mail(slug, recipient, *args, **kwargs):
    from dbmail.models import MailTemplate
    from dbmail.send_mail import SendMail

    args = (slug, recipient) + args
    try:
        import tasks

        tasks.send_db_mail.apply_async(
            args=args, kwargs=kwargs,
            priority=MailTemplate.get_template(slug=slug).priority
        )
    except ImportError:
        SendMail(*args, **kwargs).send()
