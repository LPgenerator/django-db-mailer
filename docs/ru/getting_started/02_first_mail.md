# Первое письмо за 5 минут

К концу туториала у вас будет:

- Шаблон `MailTemplate` через Django admin.
- Реальная отправка через локальный `locmem` backend (SMTP не нужен).
- Запись в `MailLog`, которую можно посмотреть.

## Предусловия

Вы прошли [3-минутную установку](01_install.md), демо или ваш проект
запускается через `python manage.py runserver`.

## 1. Настроить email backend

Для локальной отладки направьте письма в `django.core.mail.outbox`:

```python
# settings.py
EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"
DEFAULT_FROM_EMAIL = "demo@example.com"
```

В production переключайтесь на SMTP
(`django.core.mail.backends.smtp.EmailBackend`) или backend
`django-anymail` (SES / Postmark / Mailgun).

## 2. Создать отправителя и шаблон

Можно через admin, но через shell быстрее:

```python
# python manage.py shell_plus
from dbmail.models import MailFromEmail, MailTemplate

sender = MailFromEmail.objects.create(name="App", email="app@example.com")

MailTemplate.objects.create(
    name="Welcome — first hello",
    subject="Welcome, {{user}}!",
    message="""
        <h1>Привет, {{user}}</h1>
        <p>Рады, что вы с нами. Ваш тариф: <b>{{plan}}</b>.</p>
        <p>Зайдите на <a href="{{site.domain}}">наш сайт</a>.</p>
    """,
    slug="welcome",
    is_html=True,
    from_email=sender,
)
```

Заметки:

- `slug` — публичный идентификатор, который передаётся в `send_db_mail`.
- `subject` и `message` — это Django-шаблоны. Доступ к атрибутам
  через `{{ instance.field }}` разрешён; `{% load %}` и `{% include %}`
  — нет (sandbox-рендер ожидается в 3.1; до этого редактировать
  поля шаблона может **только superuser** —
  см. [модель безопасности](../../explanation/security.md)).
- При `is_html=True` и включённом `DB_MAILER_TRACK_ENABLE = True`
  встраивается tracking pixel.

## 3. Отправить

```python
from dbmail import send_db_mail

send_db_mail(
    "welcome",
    "alice@example.com",
    {"user": "Алиса", "plan": "Pro"},
    use_celery=False,
)
# → "OK"
```

Третий позиционный аргумент — словарь контекста. `use_celery=False`
запускает отправку синхронно — без него `dbmail` ставит задачу
через `apply_async`, и вызов сразу возвращается.

## 4. Проверить outbox

```python
from django.core import mail
print(len(mail.outbox))                      # → 1
print(mail.outbox[0].subject)                # → "Welcome, Алиса!"
print(mail.outbox[0].body[:80])              # → "<h1>Привет, Алиса</h1>..."
```

## 5. Проверить MailLog

```python
from dbmail.models import MailLog

log = MailLog.objects.order_by("-pk").first()
print(log.is_sent, log.template.slug, log.backend)
# → True welcome mail
```

`MailLog` также видны в admin → `/admin/dbmail/maillog/`. Можно
искать по email получателя, log_id, бэкенду, шаблону, статусу
успеха.

## 6. Несколько получателей

```python
send_db_mail("welcome", ["a@example.com", "b@example.com"], {"user": "team"}, use_celery=False)
send_db_mail("welcome", "a@example.com, b@example.com", {"user": "team"}, use_celery=False)
```

Через `MailGroup` (admin → Mail groups → Add):

```python
from dbmail.models import MailGroup, MailGroupEmail

g = MailGroup.objects.create(name="Subscribers", slug="subscribers")
MailGroupEmail.objects.bulk_create([
    MailGroupEmail(group=g, name="A", email="a@example.com"),
    MailGroupEmail(group=g, name="B", email="b@example.com"),
])
send_db_mail("welcome", "subscribers", {"user": "everyone"}, use_celery=False)
```

Аргумент `recipient` распознаётся в порядке: сначала как
`MailGroup.slug`, потом как строка через запятую, потом как список.

## Что дальше

- **[03_signals.md](03_signals.md)** — автоматическая отправка по
  `post_save` любой модели.
- **[../how_to/api_with_hmac.md](../how_to/api_with_hmac.md)** —
  отправка через HTTP API из других сервисов.
- Полный справочник полей моделей — на английском
  ([reference/models.md](https://django-db-mailer.readthedocs.io/en/latest/reference/models.html)).
