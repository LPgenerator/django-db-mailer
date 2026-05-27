# Quick install (3 minutes)

A minimal end-to-end setup that puts a working `django-db-mailer` into
a fresh Django project. For more detail see
[installation.md](../installation.md).

## 1. Install

```bash
pip install -U django-db-mailer
```

## 2. Add to `INSTALLED_APPS`

```python
# settings.py
INSTALLED_APPS = [
    ...,
    "django.contrib.sites",   # required
    "dbmail",
]
SITE_ID = 1
```

## 3. Mount the URLs

```python
# urls.py
from django.urls import include, path

urlpatterns = [
    ...,
    path("dbmail/", include("dbmail.urls", namespace="dbmail")),
]
```

## 4. Cache backend

`dbmail` aggressively caches templates / API keys / rate-limit
counters. Without a working Django cache **it will not function**.

For local development LocMem is fine:

```python
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        "LOCATION": "dbmail",
    },
}
```

For production use Redis or Memcached — see
[settings.md](../settings.md#cache-required).

## 5. Migrate

```bash
python manage.py migrate
```

`dbmail` ships exactly two migrations. `0002_apikey_hash_data` is a
no-op on a fresh database.

## 6. Verify

```bash
python manage.py shell
```

```python
from dbmail.models import MailFromEmail, MailTemplate
from dbmail import send_db_mail

sender = MailFromEmail.objects.create(name="from", email="from@example.com")
MailTemplate.objects.create(
    name="welcome",
    subject="Hi {{user}}",
    slug="welcome",
    message="Welcome, {{user}}.",
    is_html=False,
    from_email=sender,
)

send_db_mail("welcome", "you@example.com", {"user": "Alice"}, use_celery=False)
# → "OK"
```

If you see `"OK"` and a row in `Mail logs` (admin), continue with
[Your first mail in 5 minutes](02_first_mail.md).
