# Send via SendGrid / Mailgun / SES (or any SMTP relay)

`dbmail` does not bundle a SendGrid / Mailgun / SES provider — there
is no need. Configure Django's standard email backend or
`django-anymail`, and `dbmail` routes through it transparently.

## Option A — Django SMTP backend

Most third-party transactional services expose an SMTP gateway. This
is the simplest setup and does not require an extra package.

### SendGrid

```python
# settings.py
EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = "smtp.sendgrid.net"
EMAIL_PORT = 587
EMAIL_HOST_USER = "apikey"   # literal string "apikey" — SendGrid quirk
EMAIL_HOST_PASSWORD = os.environ["SENDGRID_API_KEY"]
EMAIL_USE_TLS = True
DEFAULT_FROM_EMAIL = "verified@yourdomain.com"
```

### Mailgun

```python
EMAIL_HOST = "smtp.mailgun.org"
EMAIL_PORT = 587
EMAIL_HOST_USER = "postmaster@mg.yourdomain.com"
EMAIL_HOST_PASSWORD = os.environ["MAILGUN_SMTP_PASSWORD"]
EMAIL_USE_TLS = True
```

### Amazon SES

```python
EMAIL_HOST = "email-smtp.eu-west-1.amazonaws.com"
EMAIL_PORT = 587
EMAIL_HOST_USER = os.environ["AWS_SES_USER"]
EMAIL_HOST_PASSWORD = os.environ["AWS_SES_PASSWORD"]
EMAIL_USE_TLS = True
```

`dbmail` calls `django.core.mail.get_connection()` per send and gets
the configured SMTP backend. No further wiring needed.

## Option B — Per-template credential

If different templates send via different vendors (multi-tenant SaaS,
white-label setups), attach a `MailFromEmailCredential` to each
template:

1. Admin → DBMail → Mail credentials → Add:
   - Host: `smtp.sendgrid.net`
   - Port: `587`
   - Username: `apikey`
   - Password: paste the API key (stored as plaintext at rest until 3.1)
   - Use TLS: yes
2. Admin → Mail from emails → Add: assign the credential.
3. Admin → Templates → Edit: set `from_email` to that
   `MailFromEmail` row.

The Sender opens the per-template SMTP connection instead of the
project default. Each tenant gets their own DKIM signature.

## Option C — django-anymail (HTTP API)

For higher throughput, observability, and advanced features (open
tracking, suppression lists, scheduled sends) use the vendor HTTP API
via `django-anymail`:

```bash
pip install "django-anymail[sendgrid]"
# or [mailgun] / [amazon-ses] / [postmark] / [sparkpost] / ...
```

```python
# settings.py
INSTALLED_APPS = [..., "anymail"]
EMAIL_BACKEND = "anymail.backends.sendgrid.EmailBackend"
ANYMAIL = {
    "SENDGRID_API_KEY": os.environ["SENDGRID_API_KEY"],
    "WEBHOOK_SECRET": "your:secret",
}
DEFAULT_FROM_EMAIL = "verified@yourdomain.com"
```

`dbmail` continues to call `get_connection()` and gets the anymail
backend transparently.

## Bounces, opens, deliverability

Anymail webhook integration covers events. Inside `dbmail`, the
built-in `MailLogTrack` records open events from the bundled tracking
pixel — see [tracking_pixel.md](tracking_pixel.md). The two are
complementary: anymail sees "the vendor accepted the message",
`MailLogTrack` sees "the recipient opened the message in their mail
client".

## Verifying

```python
from dbmail import send_db_mail
send_db_mail("welcome", "you@yourdomain.com", {"user": "Test"}, use_celery=False)
# Check the vendor dashboard — message should arrive within seconds.
```

Stuck on `Connection refused`? `dbmail` calls `get_connection()` at
send time — restart your runserver / celery worker after editing
`settings.py`.

## See also

- [settings.md](../settings.md#smtp) — SMTP project settings.
- [reference/models.md](../reference/models.md#mailfromemailcredential)
  — per-template credential row.
- [Security model](../explanation/security.md) — plaintext-at-rest caveat for
  `MailFromEmailCredential.password`.
