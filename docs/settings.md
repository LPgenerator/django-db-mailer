# Project settings

`dbmail` does not own your Django project — it asks you to configure
the Django facilities it depends on (cache, email, Celery,
optional integrations) and exposes its own knobs prefixed
`DB_MAILER_*`. The latter are documented separately in
[app_settings.md](app_settings.md); this file covers the project-level
plumbing.

## Cache (required)

`dbmail` aggressively caches `MailTemplate`, `MailGroup`, `ApiKey`,
and rate-limit counters. **It will not function without a working
Django cache backend.**

```bash
pip install redis hiredis              # built-in redis backend
# or
pip install pymemcache                  # built-in memcached backend
```

```python
# settings.py — Django ≥ 4.0 ships built-in Redis support
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.redis.RedisCache",
        "LOCATION": "redis://127.0.0.1:6379/2",
    },
}

# Or memcached (PyMemcacheCache is the modern Django default)
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.memcached.PyMemcacheCache",
        "LOCATION": "127.0.0.1:11211",
    },
}

# Or LocMem for unit tests
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        "LOCATION": "dbmail",
    },
}
```

`django-pylibmc` and `django-redis-cache` are unmaintained — use the
built-in Django backends instead.

## SMTP

Project-level defaults Django uses for any `send_mail` call:

```python
EMAIL_HOST = "smtp.gmail.com"
EMAIL_PORT = 587
EMAIL_HOST_USER = "noreply@example.com"
EMAIL_HOST_PASSWORD = "your-app-password"
EMAIL_USE_TLS = True
DEFAULT_FROM_EMAIL = "Site <noreply@example.com>"
```

For multi-tenant setups attach a per-template
`MailFromEmailCredential` row in the admin instead of touching
`settings.py`. The admin form uses a password widget and stores the
credential in the database (stored as plaintext at rest until 3.1 —
see [security model](explanation/security.md) for details).

## Celery (required for async + scheduled delivery)

`dbmail` does not bundle Celery; install the optional extra:

```bash
pip install "django-db-mailer[celery]"
```

Minimal `settings.py`:

```python
CELERY_BROKER_URL = "redis://127.0.0.1:6379/1"
CELERY_RESULT_BACKEND = "redis://127.0.0.1:6379/2"
CELERY_TASK_DEFAULT_QUEUE = "default"
CELERY_TASK_ACKS_LATE = True
CELERY_WORKER_PREFETCH_MULTIPLIER = 1   # SMTP-friendly
CELERY_TASK_SERIALIZER = "json"          # do NOT use pickle
CELERY_RESULT_SERIALIZER = "json"
```

Demo project layout (see `demo/demo/celery.py`):

```python
# demo/celery.py
import os
from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "demo.settings")
app = Celery("demo")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()
```

```bash
celery -A demo worker -l info -Q default
celery -A demo beat -l info             # for scheduled deferred-signal cron
```

`django-celery` (the legacy Django-Celery integration package) was
discontinued by upstream in 2018 — do not install it.

`dbmail` routes per-channel queues via
`DB_MAILER_PUSH_QUEUE / SMS_QUEUE / TTS_QUEUE / BOT_QUEUE / SIGNALS_QUEUE / TRACKING_QUEUE`
(see [app_settings.md](app_settings.md)). Run dedicated workers if you
expect high SMS/push volume:

```bash
celery -A demo worker -Q sms_messages -n sms@%h -c 2
celery -A demo worker -Q push_messages -n push@%h -c 4
celery -A demo worker -Q default -n default@%h -c 4
```

## Optional integrations

### Templates revision

```bash
pip install django-reversion
```

```python
INSTALLED_APPS = [..., "reversion"]
```

The dbmail admin classes auto-detect `reversion` and replace
`ModelAdmin` with `VersionAdmin`. No further config.

### Templates compare revision

```bash
pip install django-reversion-compare diff-match-patch
```

```python
INSTALLED_APPS = [..., "reversion", "reversion_compare"]
```

### Rich-text editor

```bash
pip install django-tinymce        # OR
pip install django-ckeditor
```

```python
INSTALLED_APPS = [..., "tinymce"]
# or
INSTALLED_APPS = [..., "ckeditor"]
```

The widget is selected at import time. The schema is always `TEXT`
regardless of which (or no) widget is installed, so you can swap
freely without a migration.

If you mount TinyMCE's URLs:

```python
# urls.py
from django.urls import include, path

urlpatterns = [
    ...,
    path("tinymce/", include("tinymce.urls")),
]
```

### Premailer (CSS inliner)

```bash
pip install "django-db-mailer[html]"   # premailer + html2text
```

`dbmail.utils.premailer_transform` inlines CSS for HTML templates so
they render correctly in clients that strip `<style>` blocks. Failure
falls back to the original HTML with a `WARN` log line.

### Admin theme

```bash
pip install django-grappelli
```

```python
INSTALLED_APPS = ["grappelli", ..., "django.contrib.admin"]
```

`django-suit` is unmaintained — Grappelli is the supported skin.

### Translation (multilingual templates)

```bash
pip install django-modeltranslation
```

```python
MODELTRANSLATION_DEFAULT_LANGUAGE = "en"
MODELTRANSLATION_LANGUAGES = ("en", "ru")
MODELTRANSLATION_TRANSLATION_FILES = ("dbmail.translation",)

INSTALLED_APPS = [
    "modeltranslation",      # must be BEFORE django.contrib.admin
    ...,
    "django.contrib.admin",
]

# If using grappelli, add grappelli_modeltranslation as well:
INSTALLED_APPS = [
    "grappelli",
    "grappelli_modeltranslation",
    "modeltranslation",
    ...,
]
```

```bash
python manage.py collectstatic
python manage.py sync_translation_fields --noinput
```

### Tracking (open-rate pixel + UA + GeoIP)

```bash
pip install "django-db-mailer[tracking]"   # httpagentparser
pip install geoip2                          # optional GeoIP
```

`django-ipware` is now a hard dependency of `dbmail` (replaced the
hand-rolled XFF parser in 3.0) — you no longer install it
explicitly.

```python
DB_MAILER_TRACK_ENABLE = True
DB_MAILER_ENABLE_LOGGING = True
```

Tracking templates **must** be HTML (not plain text). Celery workers
must be running. Django's `Site` framework must resolve to a real
domain — the tracking URL is built from `Site.objects.get_current()`.
`MaxMind` GeoIP database must be installed for `MailLogTrack.country` /
`city` enrichment to populate.

## URLs

```python
# urls.py
from django.urls import include, path

urlpatterns = [
    ...,
    path("dbmail/", include("dbmail.urls", namespace="dbmail")),
]
```

URL names are namespaced under `dbmail:` since 3.0 — see
[MIGRATION.md](../MIGRATION.md#url-names-are-now-namespaced).

## See also

- [app_settings.md](app_settings.md) — every `DB_MAILER_*` knob.
- [Security model](explanation/security.md) — known limitations and threat model.
- [api.md](api.md) — public HTTP endpoint hardening (rate limit, HMAC, kill switch).
