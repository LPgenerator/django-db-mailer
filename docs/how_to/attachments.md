# Attachments

`dbmail` accepts attachments via two paths: per-call kwargs (transient
files) and per-template `MailFile` rows (recurring assets like a PDF
brochure attached to every welcome email).

## Per-call attachments

```python
from dbmail import send_db_mail

# (filename, content, mimetype) tuples — Django convention
send_db_mail(
    "invoice",
    "customer@example.com",
    {"order": order},
    attachments=[
        ("invoice.pdf", pdf_bytes, "application/pdf"),
        ("receipt.txt", "Thank you!", "text/plain"),
    ],
)

# Or paths — content is read at send time
send_db_mail(
    "promo",
    "user@example.com",
    files=["/var/www/static/brochure.pdf", "/var/www/static/photo.jpg"],
)
```

`attachments=` is the canonical Django EmailMessage shape.
`files=` is a `dbmail` shortcut that reads file paths and resolves
mimetype via stdlib `mimetypes`.

## Per-template attachments (`MailFile`)

For files that should be attached every time a template fires (PDF
guide, tax form, T&C), upload them through the admin:

1. Open `/admin/dbmail/mailtemplate/<id>/change/`.
2. Scroll to the **Mail files** inline.
3. Click **Add another mail file** → choose file → save.

The Sender attaches every active `MailFile` row before injecting the
optional per-call attachments.

```python
# settings.py — where MailFile.filename is uploaded
MEDIA_ROOT = "/var/lib/django-uploads/"
MEDIA_URL = "/uploads/"
DB_MAILER_UPLOAD_TO = "mail_files"   # subfolder inside MEDIA_ROOT
```

## Programmatic upload

```python
from django.core.files.base import ContentFile
from dbmail.models import MailFile, MailTemplate

template = MailTemplate.objects.get(slug="welcome")
MailFile.objects.create(
    template=template,
    name="Welcome guide",
    filename=ContentFile(pdf_bytes, name="welcome.pdf"),
)
```

## Limits

- The Sender reads file content into memory before passing to
  `EmailMessage` — large attachments will pin RAM. Document a 10 MB
  practical cap in your project's runbook.
- The bundled tracking pixel (1×1 GIF) is appended to HTML body, not
  to attachments — it does not interact with `MailFile`.
- HTML inline images: pass them through the standard Django
  `EmailMessage.attach()` pattern via a custom backend if you need
  `cid:` references.

## Removing per-template attachments

```python
from dbmail.models import MailFile

MailFile.objects.filter(template__slug="welcome").delete()
```

The `MEDIA_ROOT` files on disk are **not** removed automatically (DB
delete only). If disk cleanup matters, override `MailFile.delete()`
or run `django-cleanup` in your project.

## Testing

```python
# tests/test_attachments.py
from django.core import mail
from dbmail import send_db_mail


def test_per_call_attachment_lands_in_outbox(db, mail_template, settings):
    settings.EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"
    mail.outbox.clear()

    send_db_mail(
        mail_template.slug,
        "you@example.com",
        attachments=[("note.txt", "hi", "text/plain")],
        use_celery=False,
    )

    msg = mail.outbox[0]
    assert msg.attachments == [("note.txt", "hi", "text/plain")]
```

## See also

- [usage.md](../usage.md) — full kwargs reference for `send_db_mail`.
- [reference/models.md](../reference/models.md) — `MailFile` field
  list.
- [Django EmailMessage docs](https://docs.djangoproject.com/en/stable/topics/email/#sending-multiple-emails)
