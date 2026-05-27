# Установка

## Совместимость

| Python | Django |
|---|---|
| 3.10, 3.11, 3.12 | 4.2 LTS, 5.2 LTS |
| 3.13, 3.14 | 5.2 LTS, 6.0 |

PyPy **не поддерживается**. Python ≤ 3.9 и Django ≤ 4.1 не
поддерживаются в `3.0` — если вы не можете обновить рантайм,
оставайтесь на ветке `2.4.x`.

## Установка через pip

```bash
pip install -U django-db-mailer
```

Для SDK провайдеров доустанавливайте соответствующие extras
(импортируются лениво — только то, что вы реально используете):

```bash
pip install "django-db-mailer[apns]"          # apple/apns2 (HTTP/2 push)
pip install "django-db-mailer[fcm]"           # firebase / google
pip install "django-db-mailer[twilio]"        # Twilio SMS
pip install "django-db-mailer[pubnub]"        # pubnub>=7
pip install "django-db-mailer[brevo]"         # Brevo (бывший Sendinblue)
pip install "django-db-mailer[webpush]"       # pywebpush
pip install "django-db-mailer[html]"          # html2text + premailer
pip install "django-db-mailer[tracking]"      # httpagentparser
pip install "django-db-mailer[celery]"        # celery + redis
pip install "django-db-mailer[all-providers]" # всё сразу
```

На production не забудьте собрать статику:

```bash
python manage.py collectstatic
```

## Настройки Django

```python
INSTALLED_APPS = [
    ...
    "django.contrib.sites",
    "dbmail",
    ...
]
SITE_ID = 1
```

Фреймворк `Site` обязателен — `dbmail` читает
`Site.objects.get_current()` для построения URL tracking pixel и
контекста рендера шаблона.

Подключите URL-маршруты (имена — в namespace `dbmail:`):

```python
# urls.py
from django.urls import include, path

urlpatterns = [
    ...
    path("dbmail/", include("dbmail.urls", namespace="dbmail")),
]
```

## База данных

```bash
python manage.py migrate
```

`3.0` поставляет ровно две миграции — `0001_initial.py` (финальная
схема) и `0002_apikey_hash_data.py` (бэкфилл хеша на pre-3.0 ключах).
Обе — no-op для свежей установки.

Если вы апгрейдитесь с `2.x` — **оставайтесь на 2.4.x**.
Автоматического пути миграции 2.x → 3.0 нет (clean break).
См. [MIGRATION.md](https://github.com/LPgenerator/django-db-mailer/blob/master/MIGRATION.md).

## Опциональные интеграции

`dbmail` дружит с рядом сторонних Django-приложений, если они
установлены и перечислены в `INSTALLED_APPS`. Ничего из этого не
обязательно.

```python
INSTALLED_APPS = [
    ...
    "ckeditor",                       # rich-text виджет для MailTemplate.message
    # либо "tinymce",                 # альтернативный виджет
    "modeltranslation",               # многоязычный MailTemplate
    "grappelli",                      # тема админки
    "reversion",                      # история версий
    "reversion_compare",              # сравнение версий в админке
    ...
]
```

HTML-виджет выбирается на момент импорта — если установлен `tinymce`,
он побеждает; иначе `ckeditor`; иначе обычный `TextField`. Колонка БД
всегда `TEXT` независимо от виджета — можно менять виджет без
миграций.

## Проверка установки

```python
# Django shell
from dbmail import send_db_mail
from dbmail.models import MailFromEmail, MailTemplate

sender = MailFromEmail.objects.create(name="from", email="from@example.com")
MailTemplate.objects.create(
    name="Welcome",
    subject="Welcome {{user}}",
    slug="welcome",
    message="Hello {{user}}",
    is_html=False,
    from_email=sender,
)

send_db_mail("welcome", "you@example.com", {"user": "Alice"}, use_celery=False)
# → "OK"
```

Если вызов вернул `"OK"` и появилась запись в Django admin →
`Mail logs`, установка завершена. Дальше:
[5-минутный туториал](getting_started/02_first_mail.md).

## Дальнейшие шаги

- [Быстрый старт](getting_started/01_install.md) — первый шаблон за
  3 минуты.
- [Первая отправка](getting_started/02_first_mail.md) — пошаговый
  туториал.
- [Сигналы по событиям моделей](getting_started/03_signals.md) —
  автоотправка на `post_save` и других сигналах.
