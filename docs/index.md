# django-db-mailer

> 🇷🇺 **Русскоязычная версия:** [docs/ru/index.md](ru/index.md) — getting started + installation + cookbook на русском.
> 🇬🇧 **English version below.**

A Django battery for managing email / SMS / push / TTS / bot
templates in the database, sending them through 20+ providers, and
observing every send through structured logs and an open-rate
tracking pixel.

**Highlights:**

- Templates live in the Django admin — non-developers can edit
  copy without a deploy.
- Multi-channel: SMTP, push (APNs / FCM / Web Push / Safari),
  SMS (Twilio / Nexmo / SmsAero / IQSMS / SmsBliss), TTS,
  bots (Telegram / Slack).
- DB-driven `Signal` rows wire Django dispatch (`post_save`, …) to
  templates without writing code.
- `Sender` lifecycle: priority, retries, language, custom from-emails,
  per-template SMTP credentials, attachments, BCC.
- Hardened public HTTP API: hashed key, rate limit, optional HMAC,
  provider allowlist, kill switch.
- Open-rate tracking, MailLog, MailLogTrack with UA + GeoIP
  enrichment.
- Celery 5 integration for async + scheduled delivery.
- Helm chart + Docker compose ready.

## Quick start

```{toctree}
:caption: Getting started
:maxdepth: 1
getting_started/01_install
getting_started/02_first_mail
getting_started/03_signals
```

## How-to recipes

```{toctree}
:caption: How-to
:maxdepth: 1
how_to/send_via_sendgrid
how_to/api_with_hmac
how_to/rotate_apikey
how_to/tracking_pixel
how_to/multilingual_templates
how_to/attachments
how_to/deferred_signals
how_to/import_csv_to_mailgroup
how_to/add_custom_provider
how_to/test_custom_backend
how_to/deploy_helm
```

## Architecture & explanation

```{toctree}
:caption: Architecture
:maxdepth: 1
explanation/architecture
explanation/sender_lifecycle
explanation/signal_pipeline
explanation/celery_and_dispatch
explanation/caching
explanation/security
```

## Reference

```{toctree}
:caption: Reference
:maxdepth: 1
installation
usage
api
settings
app_settings
commands
signals
web_push
providers
custom_backends_and_providers
reference/models
```

## Development

```{toctree}
:caption: Development
:maxdepth: 1
dev_install
demo
contributing
authors
```

## Russian translation

```{toctree}
:caption: Русская версия
:maxdepth: 1
ru/index
```

## Contributing

The latest source lives on the `master` branch at
[GitHub](https://github.com/LPgenerator/django-db-mailer).

Feel free to submit
[issues](https://github.com/LPgenerator/django-db-mailer/issues);
pull requests are welcome.

Read [contributing.md](contributing.md) for the contributor checklist.

## Security

`dbmail` is a battery exposed on a public URL. Before deploying,
review the [security model](explanation/security.md): hashed
credentials, rate limiting, optional HMAC body signature, SSTI
mitigation, kill switch, and the residual risks scheduled for
`3.1` / `4.0`.

## Compatibility

| Python | Django |
|---|---|
| 3.10, 3.11, 3.12 | 4.2 LTS, 5.2 LTS |
| 3.13, 3.14 | 5.2 LTS, 6.0 |

Verified by `tox` matrix on every release. Older runtimes (Python ≤
3.9 / Django ≤ 4.1) are dropped from `3.0`; stay on the `2.4.x` line
if you cannot upgrade.
