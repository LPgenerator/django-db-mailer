# Architecture overview

`django-db-mailer` is a Django battery that turns the database into the
single source of truth for everything an outbound message needs:
template body, recipient list, sender identity, SMTP credentials,
provider routing, retry policy, audit trail. Application code
references a `MailTemplate.slug`; the framework carries the slug
through render → send → log.

## What problem space dbmail covers

```mermaid
flowchart LR
    biz[Business code] -->|send_db_mail<br/>send_db_sms<br/>send_db_push] db[(Django DB)]
    db -->|MailTemplate<br/>MailFromEmail<br/>Signal] sender[Sender]
    sender -->|render Template<br/>store MailLog] db
    sender -->|EmailMessage] smtp[SMTP relay]
    sender -->|HTTPS] vendors[Twilio / Slack /<br/>FCM / APNs / ...]
    smtp --> recipient[Recipient]
    vendors --> recipient
    recipient -->|opens HTML<br/>tracking pixel] track[/dbmail/tracker/]
    track -->|MailLogTrack] db
```

Three orthogonal concerns the package owns:

- **Authoring** — non-developers edit `MailTemplate.subject` /
  `message` in Django admin without redeploys.
- **Delivery** — five backends (mail / sms / tts / push / bot) over
  ~20 providers; one Sender lifecycle.
- **Observability** — every send writes `MailLog` + `MailLogEmail`;
  every open writes / increments `MailLogTrack`.

## When to pick dbmail (and when not)

|  | dbmail | django.core.mail | django-anymail | django-post_office |
|---|---|---|---|---|
| Templates in DB | ✅ | ❌ (file-based) | ❌ | ✅ |
| Multi-channel (SMS / push / TTS / bot) | ✅ | ❌ | ❌ | ❌ |
| DB-driven signals (auto-fire) | ✅ | ❌ | ❌ | ❌ |
| Open tracking | ✅ | ❌ | partial (vendor side) | ❌ |
| Vendor HTTP API | partial | ❌ | ✅ (best-in-class) | ❌ |
| Deferred / scheduled | ✅ | ❌ | ❌ | ✅ |
| Audit trail | ✅ | ❌ | ✅ | ✅ |

Pick **dbmail** when:

- Marketing / support edits copy without dev review.
- Multi-channel (email + SMS + push) inside one stack.
- DB-driven `Signal` rows replace hand-wired post_save handlers.
- Per-tenant SMTP credentials.

Pick **django-anymail** instead when the priority is vendor-side
analytics (SES, SendGrid, Mailgun) and templates can stay in code.

Pick **django-post_office** when you need queue-only delivery without
the multi-channel apparatus.

## Layered architecture

```mermaid
flowchart TB
    subgraph "Public API surface"
        api[send_db_mail / send_db_sms / send_db_push / send_db_tts /<br/>send_db_bot / send_db_subscription]
        view[/dbmail/api/<br/>view: send_by_dbmail]
    end

    subgraph "Dispatcher"
        dbsender[db_sender<br/>celery_supported + use_celery + template.is_active branches]
    end

    subgraph "Backends (one Sender subclass each)"
        mail_backend[backends/mail.py:Sender]
        sms_backend[backends/sms.py:Sender]
        push_backend[backends/push.py:Sender]
        tts_backend[backends/tts.py:Sender]
        bot_backend[backends/bot.py:Sender]
    end

    subgraph "Providers (~20)"
        mail_provider[smtp / sendinblue / ...]
        sms_provider[twilio / nexmo / iqsms / smsaero / smsbliss / ...]
        push_provider[apns2 / fcm / pubnub / pushover / pushall / ...]
        bot_provider[telegram / slack / ...]
    end

    subgraph "Persistence"
        db[(Django DB)]
        cache[(Redis / Memcached / locmem)]
    end

    subgraph "Async"
        celery[Celery worker]
        beat[Celery beat /<br/>send_dbmail_deferred_signal cron]
    end

    api --> dbsender
    view --> dbsender
    dbsender --> celery
    dbsender --> mail_backend
    celery --> mail_backend
    mail_backend --> mail_provider
    sms_backend --> sms_provider
    push_backend --> push_provider
    bot_backend --> bot_provider
    mail_backend --> db
    mail_backend --> cache
    beat --> celery
```

## Public API anatomy (`dbmail/__init__.py`)

The 7 exported functions are thin wrappers around `db_sender`:

| Function | Backend | Pre-set kwargs |
|---|---|---|
| `send_db_mail(slug, recipient, *args, **kwargs)` | `BACKEND['mail']` | — |
| `send_db_sms(slug, recipient, *args, **kwargs)` | `BACKEND['sms']` | — |
| `send_db_push(slug, recipient, *args, **kwargs)` | `BACKEND['push']` | — |
| `send_db_tts(slug, recipient, *args, **kwargs)` | `BACKEND['tts']` | — |
| `send_db_bot(slug, recipient, *args, **kwargs)` | `BACKEND['bot']` | — |
| `send_db_subscription(slug, user_id=None, **kwargs)` | resolves via `MailSubscription` | iterates over user's subscriptions |
| `db_sender(slug, recipient, *args, **kwargs)` | inner dispatcher | reads `template.is_active`, branches sync vs Celery |

`db_sender` flow (`dbmail/__init__.py:60-102`):

```mermaid
flowchart LR
    enter[db_sender called]
    enter --> is_active{template.is_active?}
    is_active -->|False| ret_none[return None]
    is_active -->|True| celery_check{celery_supported<br/>+ use_celery=True?}
    celery_check -->|True| celery[apply_async on db_sender task]
    celery_check -->|False| sync[Sender(...).send(is_celery=False)]
    celery --> ok[return 'OK']
    sync --> ok
```

## Helper exports

Public for backwards compatibility (used by external code that
extends dbmail):

- `app_installed(name)` — checks `INSTALLED_APPS` membership.
- `celery_supported()` — `True` iff `celery` is importable AND
  `DB_MAILER_ENABLE_CELERY = True`.
- `import_by_string(dotted)` — `importlib.import_module` shortcut.
- `get_model(app, model)` — `django.apps.get_model` shortcut.
- `get_version()` — returns `__version__` string.
- `initial_signals()` — re-runs Signal-row → dispatch.connect wiring.

Removed from 3.0 (see [MIGRATION.md](../../MIGRATION.md)):

- `import_module`, `PY3`, `python_2_unicode_compatible`,
  `default_app_config`.

## Migration story

3.0 wipes the 17-migration history accumulated in the 2.x line and
ships exactly two:

- `0001_initial.py` — final schema (BigAutoField, JSONField+pickle
  dual-write, hashed ApiKey, indexes).
- `0002_apikey_hash_data.py` — RunPython no-op on fresh DBs;
  populates `password_hash` for legacy plain `api_key` rows when
  upgrading.

There is no automated 2.x → 3.0 path — see [MIGRATION.md](../../MIGRATION.md)
for the optional manual `dumpdata`/`loaddata` recipe.

## Cross-references

- [sender_lifecycle.md](sender_lifecycle.md) — what happens inside
  one `db_sender` call.
- [signal_pipeline.md](signal_pipeline.md) — DB-driven Signal model.
- [caching.md](caching.md) — cache keys + invalidation.
- [security.md](security.md) — threat model + defence-in-depth.
- [../reference/models.md](../reference/models.md) — every model
  field with its meaning.
