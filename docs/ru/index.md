# django-db-mailer (русская версия)

Django-батарейка для управления шаблонами email / SMS / push / TTS /
бот-сообщений в базе данных, отправки через 20+ провайдеров и
наблюдения за каждой отправкой через структурированные логи и
tracking pixel для измерения открытий.

> Это сокращённая русская версия документации. Полный справочник
> (`reference/`, описание архитектуры) — только на английском.
> Переключиться на английскую версию: `/en/latest/`.

**Главное:**

- Шаблоны хранятся в Django admin — нетехнические сотрудники могут
  редактировать тексты без релиза.
- Многоканальность: SMTP, push (APNs / FCM / Web Push / Safari),
  SMS (Twilio / Nexmo / SmsAero / IQSMS / SmsBliss), TTS,
  боты (Telegram / Slack).
- Запись `Signal` в БД связывает Django dispatch (`post_save`, …) с
  шаблоном — без написания кода.
- Жизненный цикл `Sender`: приоритеты, повторы, язык, кастомные
  отправители, SMTP-учётки на шаблон, вложения, BCC.
- Усиленный публичный HTTP API: хешированный ключ, rate limit,
  опциональный HMAC, allow-list провайдеров, kill-switch.
- Учёт открытий, MailLog, MailLogTrack с обогащением UA + GeoIP.
- Интеграция с Celery 5 для асинхронной и отложенной доставки.
- Готовый Helm-чарт + docker compose.

## Быстрый старт

```{toctree}
:caption: Быстрый старт
:maxdepth: 1
getting_started/01_install
getting_started/02_first_mail
getting_started/03_signals
```

## Установка

```{toctree}
:caption: Установка
:maxdepth: 1
installation
```

## Рецепты

```{toctree}
:caption: Рецепты
:maxdepth: 1
how_to/send_via_sendgrid
how_to/api_with_hmac
how_to/rotate_apikey
how_to/tracking_pixel
how_to/import_csv_to_mailgroup
```

## Что не переведено

Часть документации — техническая и предполагает свободное чтение
английского:

- Полный справочник API (`reference/`) — поля моделей, настройки.
- Описание архитектуры.
- Гайд по custom backends.
- Документация провайдеров.

См. английскую версию: <https://django-db-mailer.readthedocs.io/en/latest/>.

## Безопасность

`dbmail` — батарейка, выставленная в публичный URL. Перед
production-deploy ознакомьтесь с [моделью безопасности](../explanation/security.md).

## Совместимость

| Python | Django |
|---|---|
| 3.10, 3.11, 3.12 | 4.2 LTS, 5.2 LTS |
| 3.13, 3.14 | 5.2 LTS, 6.0 |

Проверяется матрицей `tox` на каждом релизе. Старые рантаймы
(Python ≤ 3.9 / Django ≤ 4.1) не поддерживаются в `3.0` —
оставайтесь на ветке `2.4.x`, если не можете обновить рантайм.
