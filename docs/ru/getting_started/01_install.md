# Быстрая установка (3 минуты)

Минимальная настройка `django-db-mailer` в свежем Django-проекте.
Подробнее см. [installation.md](../installation.md).

## 1. Установить пакет

```bash
pip install -U django-db-mailer
```

## 2. Добавить в `INSTALLED_APPS`

```python
# settings.py
INSTALLED_APPS = [
    ...,
    "django.contrib.sites",   # обязательно
    "dbmail",
]
SITE_ID = 1
```

## 3. Подключить URL

```python
# urls.py
from django.urls import include, path

urlpatterns = [
    ...,
    path("dbmail/", include("dbmail.urls", namespace="dbmail")),
]
```

## 4. Кеш

`dbmail` агрессивно кеширует шаблоны / API-ключи / счётчики
rate-limit. **Без работающего кеша не запустится.**

Для локальной разработки достаточно LocMem:

```python
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        "LOCATION": "dbmail",
    },
}
```

В production используйте Redis или Memcached — см.
[settings.md](../../settings.md#cache-required) (на английском).

## 5. Миграция

```bash
python manage.py migrate
```

Поставляются ровно две миграции. `0002_apikey_hash_data` — no-op для
свежей БД.

## 6. Проверка

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

Если видите `"OK"` и появилась строка в `Mail logs` (admin), всё
работает. Дальше — [Первое письмо за 5 минут](02_first_mail.md).
