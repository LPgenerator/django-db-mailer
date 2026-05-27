# Отправка через SendGrid / Mailgun / SES (любой SMTP-релей)

`dbmail` не поставляет провайдеров для SendGrid / Mailgun / SES —
это и не нужно. Настройте стандартный Django email backend или
`django-anymail`, и `dbmail` прозрачно через него отправит.

## Вариант A — Django SMTP backend

Большинство транзакционных сервисов имеют SMTP-шлюз. Это самая
простая настройка — без дополнительных пакетов.

### SendGrid

```python
# settings.py
EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = "smtp.sendgrid.net"
EMAIL_PORT = 587
EMAIL_HOST_USER = "apikey"   # буквальная строка "apikey" — особенность SendGrid
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

`dbmail` вызывает `django.core.mail.get_connection()` на каждую
отправку и получает настроенный SMTP backend. Никакой дополнительной
конфигурации не нужно.

## Вариант Б — учётка на шаблон

Если разные шаблоны должны слать через разных вендоров (мульти-
тенант SaaS, white-label), привяжите `MailFromEmailCredential` к
каждому шаблону:

1. Admin → DBMail → Mail credentials → Add:
   - Host: `smtp.sendgrid.net`
   - Port: `587`
   - Username: `apikey`
   - Password: вставьте ключ (хранится в открытом виде до версии 3.1)
   - Use TLS: yes
2. Admin → Mail from emails → Add: привяжите credential.
3. Admin → Templates → Edit: установите `from_email` на этот
   `MailFromEmail`.

`Sender` откроет SMTP-соединение на конкретный шаблон вместо
проектного дефолта. Каждый тенант получит свою DKIM-подпись.

## Вариант В — django-anymail (HTTP API)

Для большего throughput, observability и продвинутых фич
(open tracking, suppression lists, отложенная отправка)
используйте HTTP API вендора через `django-anymail`:

```bash
pip install "django-anymail[sendgrid]"
# или [mailgun] / [amazon-ses] / [postmark] / [sparkpost] / ...
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

`dbmail` продолжает вызывать `get_connection()` и прозрачно получает
backend anymail.

## Бэунсы, открытия, доставляемость

Webhook anymail покрывает события на стороне вендора. Внутри
`dbmail` встроенный `MailLogTrack` фиксирует открытия через
tracking pixel — см. рецепт
[tracking_pixel.md](tracking_pixel.md). Они дополняют друг друга:
anymail видит "вендор принял сообщение", `MailLogTrack` видит
"получатель открыл сообщение в почтовом клиенте".

## Проверка

```python
from dbmail import send_db_mail
send_db_mail("welcome", "you@yourdomain.com", {"user": "Test"}, use_celery=False)
# Загляните в дашборд вендора — сообщение должно прийти за секунды.
```

Получили `Connection refused`? `dbmail` вызывает `get_connection()`
во время отправки — перезапустите runserver / celery worker после
правки `settings.py`.
