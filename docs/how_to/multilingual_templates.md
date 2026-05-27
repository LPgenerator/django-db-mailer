# Multilingual templates

`dbmail` supports per-language `MailTemplate.subject` / `message` via
[django-modeltranslation](https://django-modeltranslation.readthedocs.io/).
A single `MailTemplate` slug holds a translation per language; the
Sender picks the right one based on the active locale.

## 1. Install + register

```bash
pip install django-modeltranslation
```

```python
# settings.py
MODELTRANSLATION_DEFAULT_LANGUAGE = "en"
MODELTRANSLATION_LANGUAGES = ("en", "ru", "es")
MODELTRANSLATION_TRANSLATION_FILES = (
    "dbmail.translation",   # ships built-in for MailTemplate / MailBaseTemplate
)

INSTALLED_APPS = [
    "modeltranslation",     # MUST be before django.contrib.admin
    ...,
    "dbmail",
    "django.contrib.admin",
]
```

If you use `django-grappelli`, add `grappelli_modeltranslation` too —
otherwise the language tabs do not render.

## 2. Sync schema

```bash
python manage.py collectstatic
python manage.py sync_translation_fields --noinput
python manage.py update_translation_fields
```

`sync_translation_fields` adds `subject_en`, `subject_ru`,
`subject_es`, `message_en`, `message_ru`, `message_es` columns
to `dbmail_mailtemplate` (and the same for `MailBaseTemplate`).

`update_translation_fields` copies existing untranslated values into
the default-language column.

## 3. Author per-language copy

In admin, the `MailTemplate` change form now shows tabs for each
configured language. Fill in subject + message for each.

Empty translations fall back to `MODELTRANSLATION_DEFAULT_LANGUAGE`.

## 4. Send in the right language

The `language` kwarg switches the active locale during render:

```python
from dbmail import send_db_mail

# Send the Russian version
send_db_mail("welcome", "user@example.com", {"user": "Иван"}, language="ru")

# Send the English version (default)
send_db_mail("welcome", "user@example.com", {"user": "John"}, language="en")
```

The Sender wraps `Template.render` in `translation.override(language)`
so `{% trans %}` tags inside the template body also resolve. After
the render the previous active locale is restored — there is no
language leak across Celery tasks (this was a real 3.0 bug, now fixed).

## 5. Per-user automatic language

Common pattern: pull the language from the user instance.

```python
from dbmail import send_db_mail

def notify_user(user, slug, context=None):
    send_db_mail(
        slug,
        user.email,
        context or {},
        language=user.profile.language or "en",
    )
```

For a Signal-driven send, write the language picker into the
`Signal.rules` field (renders with `instance` in scope) — or, simpler,
configure your `LANGUAGE_CODE` middleware to respect the recipient.

## 6. Translating fixtures

The bundled responsive base templates (`dbmail/fixtures/mailgun_base_templates.json`)
ship in English. If you load them via `python manage.py load_dbmail_base_templates`,
duplicate the rows manually and translate `message_ru`, `message_es`, etc.

## See also

- [django-modeltranslation docs](https://django-modeltranslation.readthedocs.io/)
- [reference/models.md](../reference/models.md#mailtemplate)
- [settings.md](../settings.md#translation-multilingual-templates)
