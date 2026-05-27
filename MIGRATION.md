# Migration guide: 2.x → 3.0

`django-db-mailer 3.0` is a **clean break** from the `2.x` line. There
is no automated upgrade path. The migration history was wiped, the
Python/Django matrix moved forward by ~6 years, the public API trimmed
its Python-2 / old-Django shims, and a number of provider modules
gained or lost dependencies.

If you are starting a brand-new project on 3.0, ignore this file —
just `pip install django-db-mailer` and `manage.py migrate`.

If you have an existing 2.x install, **stay on the 2.4.x line**:

```bash
pip install "django-db-mailer<3"
```

The 2.4.x branch keeps Python ≤ 3.9 / Django ≤ 4.1 working. There
are no further releases planned on it; it is maintained at the
last-known-good state.

## Why no automated upgrade

`2.x` accumulated 17 migrations between 2015 and 2018 reflecting
schema choices from Django 1.x / 2.x and Python 2 days. Carrying them
into 3.0 alongside the new schema (`BigAutoField` PKs, `JSONField`
columns on `SignalDeferredDispatch`, hashed `ApiKey`, query indexes)
added complexity without giving real users an upgrade path most of
them would actually take. `3.0` ships exactly two migrations — `0001_initial.py`
(final schema) and `0002_apikey_hash_data.py` (data backfill no-op
on a fresh database).

## Fresh install

```bash
pip install "django-db-mailer~=3.0"
python manage.py migrate dbmail
```

That's it. Add `dbmail` to `INSTALLED_APPS` and mount the URLs (the
URL names are namespaced under `dbmail:`):

```python
# urls.py
urlpatterns = [
    path("dbmail/", include("dbmail.urls", namespace="dbmail")),
    ...
]
```

## Migrating data manually (optional)

If you absolutely need 2.x rows in a 3.0 install, dump and reload by
hand. The schema is not byte-for-byte compatible:

```bash
# On the 2.x install
python manage.py dumpdata dbmail.MailTemplate dbmail.MailFromEmail \
    dbmail.MailGroup dbmail.MailGroupEmail dbmail.MailCategory \
    dbmail.ApiKey dbmail.Signal --natural-foreign \
    --output dbmail-export.json

# On the fresh 3.0 install (after migrate dbmail)
python manage.py loaddata dbmail-export.json
```

`MailLog` / `MailLogEmail` / `MailLogTrack` rows are not portable —
schema indexes and field types changed. Operational logs from 2.x
should stay in the 2.x database; 3.0 starts a fresh history.

After loadData, hash the imported `ApiKey.api_key` values:

```bash
python manage.py shell -c "
from dbmail.models import ApiKey
for k in ApiKey.objects.filter(password_hash=''):
    k.save()  # save() populates password_hash from api_key
"
```

This is best-effort and unsupported. Production migrations should
stay on the 2.4.x line until their own retirement.

## Schema highlights

- **All PKs** are `BigAutoField`.
- **`ApiKey`** gained `password_hash`, `last_used_at`, `last_used_ip`.
  The legacy plain-text `api_key` column is kept for the 3.x line and
  removed in `4.0`.
- **`SignalDeferredDispatch`** gained `args_json`, `kwargs_json`,
  `params_json` next to the legacy pickle blobs (`BinaryField`). New
  rows are dual-written; pickle path requires
  `DB_MAILER_ALLOW_PICKLE_LEGACY=True` and is removed in `4.0`.
- **Indexes** added on `MailLog(created)`,
  `MailLog(template, is_sent)`, `MailLogTrack(mail_log, ip)`,
  `MailSubscription(address, backend)`,
  `SignalDeferredDispatch(eta, done)`.

## Code-level breaking changes

3.0 drops a number of Python 2 / old-Django compatibility shims. Most
projects will not notice, but if your code does any of these, fix it
before importing 3.0:

- `from dbmail import import_module` — **removed.** Use
  `from importlib import import_module`.
- `from dbmail import PY3` — **removed.** Python 3 is the only
  supported runtime; the constant has no meaning.
- `from dbmail import python_2_unicode_compatible` — **removed.**
  Drop the decorator; modern Django models inherit the right
  `__str__` behaviour by default.
- `default_app_config = ...` no longer required (Django ≥ 3.2 picks
  it up automatically).

## URL names are now namespaced

`dbmail/urls.py` declares `app_name = "dbmail"` in 3.0. Calls to
`reverse()` in your project must include the namespace:

```python
# 2.x
reverse("db-mail-api")
reverse("db-mail-tracker", args=[encrypted])
reverse("push-subscribe")

# 3.x
reverse("dbmail:db-mail-api")
reverse("dbmail:db-mail-tracker", args=[encrypted])
reverse("dbmail:push-subscribe")
```

Search your codebase for the exact strings `db-mail-api`,
`db-mail-tracker`, `push-subscribe`, `push-unsubscribe`. Internal
calls inside `dbmail` are already updated.

## Provider extras

Provider SDKs are now optional and lazy-imported. Install only what
you need:

```bash
pip install "django-db-mailer[apns]"          # apple/apns2
pip install "django-db-mailer[fcm]"           # firebase
pip install "django-db-mailer[twilio]"        # twilio (also raw HTTP available)
pip install "django-db-mailer[pubnub]"        # pubnub>=7
pip install "django-db-mailer[vonage]"        # vonage
pip install "django-db-mailer[brevo]"         # brevo (sendinblue successor)
pip install "django-db-mailer[sendinblue]"    # legacy mailin SDK
pip install "django-db-mailer[webpush]"       # pywebpush
pip install "django-db-mailer[html]"          # html2text + premailer
pip install "django-db-mailer[tracking]"      # httpagentparser
pip install "django-db-mailer[all-providers]" # everything
```

EOL providers (`parse_com`, `boxcar`, `prowl`, `apple/apns` legacy
binary protocol, `google/android` legacy GCM endpoint) emit a
`DeprecationWarning` on first send and are scheduled for removal in
`4.0`. They keep working in `3.x` but accept that the upstream
service is dead — the deprecation tells you to plan migration to a
replacement provider.

## Getting help

Open an issue at <https://github.com/LPgenerator/django-db-mailer/issues>
with your Django and Python versions, the database engine, and a
minimal reproducer. Do not paste credentials or real data.
