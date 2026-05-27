# Автоотправка по событиям модели (DB-driven Signal)

Каждый зарегистрированный пользователь должен получить
welcome-письмо. `dbmail` поставляет модель `Signal`, которая
связывает Django dispatch-сигналы с шаблоном — без Python-кода.

## Предусловия

Завершён [02_first_mail.md](02_first_mail.md). У вас есть рабочий
шаблон `MailTemplate` со slug'ом `welcome`.

## 1. Создать запись Signal

В Django admin: **DBMail → Signals → Add**:

| Поле | Значение |
|---|---|
| Name | `Welcome on user signup` |
| Model | `auth | user` (ContentType) |
| Signal | `post_save` |
| Template | `welcome` |
| Group | (опционально — `MailGroup` админов в BCC) |
| Rules | пусто (без дополнительного фильтра) |
| Interval | `0` (отправить сразу; ненулевое — отложит) |
| Receive once | yes (не отправлять при последующих save) |
| Update model | no (не штамповать `mail_sent` на инстансе) |
| Is active | yes |

> **Замечание о правах** — по умолчанию создавать / редактировать
> Signal могут только superuser'ы (поле `rules` рендерится через
> Django template engine против инстанса модели — та же SSTI-
> поверхность, что и `MailTemplate.message`). Sandbox-рендер
> запланирован на 3.1.

Сохраните. Новый Signal регистрируется через `initial_signals()` на
следующем запуске процесса либо немедленно через
`dbmail.signals.initial_signals()`.

## 2. Запустить

```bash
python manage.py shell
```

```python
from django.contrib.auth import get_user_model
User = get_user_model()
User.objects.create_user(username="alice", email="alice@example.com", password="x")
```

```python
from django.core import mail
print(len(mail.outbox), mail.outbox[0].subject)
# → 1 Welcome, alice!
```

Цепочка:

1. `User.save()` поднимает Django-сигнал `post_save`.
2. `dbmail.signals.signal_receiver` его получает (подключён под
   `(ContentType, signal kind)` из вашего Signal).
3. `SignalReceiver(sender, instance, ...).run()`:
   - применяет `Signal.rules` (Django-шаблонное выражение,
     отрендеренное против инстанса — пустые правила проходят).
   - вычисляет получателя из полей инстанса (по умолчанию
     `instance.email`).
   - вызывает `send_db_mail("welcome", instance.email, instance, ...)`.
4. `Sender` рендерит и ставит в очередь / отправляет.
5. Создаётся запись `MailLog`.

## 3. Опционально: отложенная отправка

Установите **Interval** > 0 (секунд) — отправка задержится.
Обработчик пишет запись `SignalDeferredDispatch` вместо
немедленной отправки. Воркер по расписанию вычерпывает очередь:

```bash
python manage.py send_dbmail_deferred_signal
```

Запускайте через cron или Celery beat — раз в минуту достаточно.

## 4. Опционально: фильтр по правилу

`Signal.rules` — это Django-шаблонное выражение, которое должно
вернуть `"True"` для срабатывания. Пример:

```jinja
{% if instance.is_active and instance.email %}True{% endif %}
```

Обработчик рендерит выражение с контекстом инстанса плюс
предыдущей сохранённой строки (`old_instance`). Используйте, чтобы
не спамить на каждый save, когда важна только конкретная транзиция:

```jinja
{% if old_instance and not old_instance.is_active and instance.is_active %}True{% endif %}
```

## 5. Опционально: пометить инстанс

Если **Update model** = yes, `dbmail` после успешной отправки ставит
флаг на инстанс — можно потом находить "пользователей, получивших
welcome". Поле флага по умолчанию `mail_sent` — добавьте его в свою
модель, если планируете использовать.

## 6. Отключить Signal

В admin сбросьте **Is active**. Django-dispatch hook остаётся
подключённым на время процесса, но receiver короткосхемится для
неактивных Signal. Для чистого отключения вызовите
`dbmail.signals.initial_signals()` ещё раз — он переподключит только
активные Signal'ы.

## 7. Что может срабатывать

Поле `Signal.signal` принимает любое имя сигнала, объявленное в
`django.db.models.signals` (`pre_save`, `post_save`, `pre_delete`,
`post_delete`, `m2m_changed`).

Кастомные сигналы из сторонних приложений (например,
`user_signed_up` от allauth) **не поддерживаются** DB-driven
потоком — подключите их явно из вашего кода и вызывайте
`send_db_mail` напрямую.

## Что дальше

- **[../how_to/api_with_hmac.md](../how_to/api_with_hmac.md)** —
  HTTP API из других сервисов.
- **[../how_to/rotate_apikey.md](../how_to/rotate_apikey.md)** —
  ротация API-ключей без даунтайма.
- **[../how_to/tracking_pixel.md](../how_to/tracking_pixel.md)** —
  учёт открытий писем.
