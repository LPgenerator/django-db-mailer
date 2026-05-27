# Учёт открытий через tracking pixel

`dbmail` встраивает прозрачный 1×1 GIF в HTML-сообщения, когда
включены оба флага: `DB_MAILER_TRACK_ENABLE = True` и
`DB_MAILER_ENABLE_LOGGING = True`. Когда получатель открывает
письмо, клиент запрашивает pixel, запрос приходит на публичный
endpoint dbmail и пишется строка `MailLogTrack`.

## Включить

```python
# settings.py
DB_MAILER_TRACK_ENABLE = True
DB_MAILER_ENABLE_LOGGING = True
```

Фреймворк Site должен резолвить реальный домен
(`Site.objects.get_current()`) — URL pixel строится от него. В
production выставьте `SITE_ID` корректно и обновите запись в
`/admin/sites/site/`.

Шаблон **должен быть HTML** (`MailTemplate.is_html = True`).
Plain-text письма не несут pixel и не создают `MailLogTrack`.

URL должны быть подключены (по умолчанию `/dbmail/...`):

```python
# urls.py
from django.urls import include, path

urlpatterns = [
    ...,
    path("dbmail/", include("dbmail.urls", namespace="dbmail")),
]
```

## Что записывается

Каждое открытие пишет / инкрементирует строку в `MailLogTrack`:

- `mail_log` (FK на MailLog)
- `counter` — счётчик открытий (растёт на каждый перезапрос)
- `is_read` — переключается в `True` при первом hit
- `ip` — резолвится через `django-ipware` (учитывает XFF +
  `IPWARE_TRUSTED_PROXY_LIST`)
- `user_agent` (raw + распарсенный: `os`, `os_version`, `dist_name`,
  `dist_version`, `browser`, `browser_version`) — заполняется
  только если установлен `httpagentparser`:
  `pip install "django-db-mailer[tracking]"`
- GeoIP-поля (`country_name`, `country_code`, `city`, `region`,
  `latitude`, `longitude`, `postal_code`, `area_code`, `dma_code`)
  — заполняются только если `geoip2` + база MaxMind настроены.

## Запрос статистики открытий

```python
from dbmail.models import MailLog, MailLogTrack
from django.db.models import Count

# Open rate по шаблону
qs = (MailLog.objects.filter(is_sent=True)
      .values("template__slug")
      .annotate(total=Count("id"), opened=Count("maillogtrack"))
      .order_by("-total"))

for row in qs:
    rate = (row["opened"] / row["total"]) * 100 if row["total"] else 0
    print(f"{row['template__slug']:30s} sent={row['total']:5d} "
          f"opens={row['opened']:5d} rate={rate:.1f}%")
```

```python
# Последние открытия по получателям
recent = (MailLogTrack.objects
          .select_related("mail_log__template")
          .order_by("-updated")[:50])

for t in recent:
    print(t.updated, t.ip, t.mail_log.template.slug, t.counter)
```

## Конфиденциальность / GDPR

`MailLogTrack` хранит PII (IP + UA + GeoIP). URL pixel шифрует только
`mail_log_id` (через Django `signing.dumps`) — адреса получателя в
URL **нет**.

Для соответствия GDPR / политике хранения запускайте clean-команду
по расписанию:

```bash
# Каждую ночь удалять tracking-строки старше DB_MAILER_LOGS_EXPIRE_DAYS
python manage.py clean_dbmail_logs
```

`DB_MAILER_LOGS_EXPIRE_DAYS` по умолчанию `7`. Подкрутите под свою
политику (например, `30` или `90`).

## Отключить для одного шаблона

Если конкретный шаблон не должен трекаться (например, ссылка
сброса пароля), установите `MailTemplate.enable_log = False` (pixel
не встроится — log_id не зарезервирован для отправки). Глобальное
отключение — `DB_MAILER_TRACK_ENABLE = False`.
