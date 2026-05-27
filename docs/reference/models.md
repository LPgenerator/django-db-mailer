# Models reference

This page enumerates every database-backed class shipped by `dbmail`,
along with field types, semantics, and cross-references. For
conceptual deep-dives see the architecture explanations (Track 4 in
the docs roadmap).

## Templates

### `MailCategory`

Optional grouping label for `MailTemplate`. No behaviour, only admin
filtering.

| Field | Type | Notes |
|---|---|---|
| `name` | CharField(50) | Unique within installation. |
| `created`, `updated` | auto timestamps | |

### `MailFromEmail`

A reusable `From:` identity. Linked to `MailTemplate.from_email`.

| Field | Type | Notes |
|---|---|---|
| `name` | CharField(100) | Sender display name. |
| `email` | EmailField | Sender address. |
| `credential` | FK(`MailFromEmailCredential`, null) | Optional SMTP credential. |

If `credential` is set, the `Sender` opens a per-template SMTP
connection using those settings instead of project-level
`EMAIL_HOST*`. Useful for multi-tenant setups where different
templates send via different mailboxes.

### `MailFromEmailCredential`

SMTP credential. **Stored as plaintext at rest** — encrypted column
lands in 3.1. See [security model](../explanation/security.md).

| Field | Type | Notes |
|---|---|---|
| `host` | CharField(50) | e.g. `smtp.gmail.com` |
| `port` | PositiveIntegerField | 25 / 465 / 587 |
| `username` | CharField(50) | optional |
| `password` | CharField(128) | optional, rendered via PasswordInput in admin |
| `use_tls` | BooleanField | |
| `fail_silently` | BooleanField | |

Admin restricted to superusers — staff cannot view or edit.

### `MailBcc`

Global BCC list. Every send copies these addresses. Per-template BCC
is on `MailTemplate.bcc_email` instead.

| Field | Type | Notes |
|---|---|---|
| `email` | EmailField | unique |
| `is_active` | BooleanField | |

### `MailBaseTemplate`

Optional wrapper used by `MailTemplate.base` to share common
HTML/header/footer across templates. The base body is concatenated
with the per-template body before render.

| Field | Type | Notes |
|---|---|---|
| `name` | CharField(50) | unique |
| `message` | HTMLField | Django template, must contain `{{content}}` for the inner body. **Superuser-only edit** (SSTI surface). |

### `MailTemplate`

The central table. Every send dispatches against a `MailTemplate.slug`.

| Field | Type | Notes |
|---|---|---|
| `name` | CharField(100) | Display name. |
| `subject` | CharField(255) | Django template, rendered against context. **Superuser-only edit.** |
| `message` | HTMLField | Body. Same. |
| `slug` | SlugField, unique | Public identifier passed to `send_db_mail("slug", ...)`. |
| `category` | FK(`MailCategory`, null) | |
| `from_email` | FK(`MailFromEmail`, null) | Optional override of `DEFAULT_FROM_EMAIL`. |
| `base` | FK(`MailBaseTemplate`, null) | Optional wrapper. |
| `bcc_email` | M2M(`MailBcc`) | Per-template BCC. |
| `interval` | PositiveIntegerField, default 60 | Seconds before retry on failure (Celery `default_retry_delay`). |
| `priority` | IntegerField, choices=PRIORITY_STEPS | High / Medium / Low / Deferred. |
| `enable_log` | BooleanField, default True | If False, only failed sends are logged. |
| `is_html` | BooleanField, default False | Drives plain vs alternative MIME. |
| `is_admin` | BooleanField, default False | Hide from regular `send_db_mail` callers; admin-only template. |
| `is_active` | BooleanField, default True | If False, `send_db_mail` returns `None` silently. |
| `num_of_retries` | PositiveIntegerField, default 1 | Sync-mode retry attempts. |
| `created`, `updated` | auto | |

Cache: per-slug, no TTL — invalidated by `_clean_cache` on save.

## Logs / observability

### `MailLog`

One row per send attempt (success or failure, depending on
`enable_log`).

| Field | Type | Notes |
|---|---|---|
| `template` | FK(`MailTemplate`) | |
| `is_sent` | BooleanField, db_index | True / False per attempt. |
| `error_message` | TextField | Truncated traceback. |
| `error_exception` | FK(`MailLogException`, null) | Classification. |
| `num_of_retries` | PositiveIntegerField | |
| `log_id` | CharField(50), db_index | UUID-shaped per send (used by tracking pixel). |
| `backend` | CharField, db_index | mail / sms / tts / push / bot. |
| `provider` | CharField, db_index | If a custom provider was used. |
| `user` | FK(USER, null) | If `user=` kwarg was passed (and stayed JSON-clean). |
| `correlation_id` | CharField(64), db_index, null | Optional business key (order ID, request ID, OpenTelemetry trace ID). Pass as `correlation_id=` kwarg to any `send_db_*` function or as a POST field to `/dbmail/api/`. |
| `created` | auto | |

Indexes: `MailLog(created)`, `MailLog(template, is_sent)` for
operational queries.

### `MailLogEmail`

Per-recipient row for each `MailLog`. One log → many emails (to /
cc / bcc).

| Field | Type | Notes |
|---|---|---|
| `log` | FK(`MailLog`) | cascade |
| `email` | CharField | recipient address |
| `mail_type` | CharField, choices=`to/cc/bcc` | |

### `MailLogTrack`

Open-rate / read-receipt enrichment. Created when a recipient hits
the tracking pixel URL.

| Field | Type | Notes |
|---|---|---|
| `mail_log` | FK(`MailLog`) | cascade |
| `counter` | PositiveIntegerField | open count |
| `is_read` | BooleanField | |
| `ip` | GenericIPAddressField | resolved via django-ipware |
| `user_agent` | CharField | |
| `os`, `os_version`, `dist_name`, `dist_version` | CharField | populated by `httpagentparser` if installed |
| `browser`, `browser_version` | CharField | |
| `country_name`, `country_code`, `country_code3` | CharField | populated by `geoip2` if installed |
| `city`, `region`, `postal_code` | CharField | |
| `latitude`, `longitude` | FloatField | |
| `area_code`, `dma_code` | IntegerField | |
| `created`, `updated` | auto | |

Indexes: `MailLogTrack(mail_log, ip)`.

### `MailLogException`

Classifier for repeated send failures. The admin lists all unique
exception class names ever logged; flagging one as `ignore=True` makes
the Sender suppress retries for that exception class.

| Field | Type | Notes |
|---|---|---|
| `name` | CharField, unique | e.g. `SMTPRecipientsRefused` |
| `ignore` | BooleanField | |

## Signals (DB-driven)

### `Signal`

Connect a Django `dispatch.Signal` (`post_save`, `pre_save`, …) to a
`MailTemplate`. Edited only by superusers (SSTI surface — `rules` is
a template expression).

| Field | Type | Notes |
|---|---|---|
| `name` | CharField(100) | display |
| `model` | FK(`ContentType`) | the model whose lifecycle fires the signal |
| `signal` | CharField, choices | `pre_save`, `post_save`, `pre_delete`, `post_delete`, `m2m_changed` |
| `template` | FK(`MailTemplate`) | what to send |
| `group` | FK(`MailGroup`, null) | optional BCC list |
| `rules` | TextField | Django template expression — must render to `"True"` for the send to fire |
| `interval` | PositiveIntegerField, default 0 | If > 0, dispatch is deferred (`SignalDeferredDispatch`). |
| `receive_once` | BooleanField | If True, dispatched at most once per (model, instance.pk). |
| `update_model` | BooleanField | If True, stamps `mail_sent` field on the instance after success. |
| `is_active` | BooleanField | |

### `SignalLog`

Tracks `(model, model_pk, signal)` triples already fired (for
`receive_once` enforcement).

### `SignalDeferredDispatch`

Queue row for non-zero `Signal.interval`. The
`send_dbmail_deferred_signal` management command drains rows whose
`eta <= now()`.

| Field | Type | Notes |
|---|---|---|
| `args`, `kwargs`, `params` | BinaryField | legacy pickle blobs (kept until 4.0 — opt-in via `DB_MAILER_ALLOW_PICKLE_LEGACY`) |
| `args_json`, `kwargs_json`, `params_json` | JSONField, nullable | new dual-write target (pickle → JSON migration) |
| `eta` | DateTimeField, db_index | when to dispatch |
| `done` | BooleanField, nullable | `NULL`=pending, `False`=in-flight, `True`=done |
| `created` | auto | |

Index: `(eta, done)` for the cron drain query.

## Groups / subscriptions

### `MailGroup`

A named list of email / phone / push tokens. Resolved when
`recipient` is a string with no `@` or `+`.

| Field | Type | Notes |
|---|---|---|
| `name` | CharField(100) | |
| `slug` | SlugField, unique | passed as `recipient` |
| `created`, `updated` | auto | |

### `MailGroupEmail`

Member of a `MailGroup`.

| Field | Type | Notes |
|---|---|---|
| `name` | CharField(100) | display |
| `email` | CharField, unique-per-group | address / phone / token |
| `group` | FK(`MailGroup`) | cascade |

### `MailSubscription`

Per-user opt-in / opt-out for a backend. Honours quiet hours.

| Field | Type | Notes |
|---|---|---|
| `user` | FK(USER, null) | nullable for guest subs |
| `address` | CharField, db_index | recipient |
| `backend` | CharField, db_index | mail / sms / push |
| `start_hour`, `end_hour` | TimeField | quiet-hours window — sends only inside |
| `defer_at_allowed_hours` | BooleanField | if True, queue for later instead of dropping |
| `is_enabled` | BooleanField | user opt-out |
| `is_checked` | BooleanField | confirmation-link verified |
| `created`, `updated` | auto | |

Index: `(address, backend)`.

### `ApiKeyUsageAudit`

Persistent audit trail for every hit on `/dbmail/api/`. One row per
request, written regardless of authentication outcome. The table is
informational — it does not gate any request processing. Admin view
is read-only.

| Field | Type | Notes |
|---|---|---|
| `api_key` | FK(`ApiKey`, null, on_delete=PROTECT) | Null when the key is missing or cannot be resolved (e.g. `missing_api_key`). |
| `api_key_name` | CharField(25) | Copy of `ApiKey.name` at write time, retained if the FK is later deleted. |
| `ip` | GenericIPAddressField | Resolved via django-ipware. |
| `ua` | CharField | `User-Agent` header. |
| `action` | CharField | One of: `kill_switch`, `missing_api_key`, `provider_blocked`, `rate_limit`, `hmac_invalid`, `invalid_key`, `bad_request`, `send`. |
| `success` | BooleanField | True only for `send`. |
| `detail` | CharField, null | First four characters of the raw key on authentication failures; `slug` on `send`. |
| `created` | auto | |

Retention and cleanup are the operator's responsibility. The bundled
`clean_dbmail_logs` management command does not touch this table.

## API

### `ApiKey`

Public API endpoint authenticator. See
[api.md](../api.md) and [security model](../explanation/security.md).

| Field | Type | Notes |
|---|---|---|
| `name` | CharField(25) | display |
| `api_key` | CharField(32), unique | legacy plaintext column (kept for 3.x, removed in 4.0) |
| `password_hash` | CharField(255) | Django `make_password` output (Argon2 / PBKDF2) |
| `is_active` | BooleanField | |
| `last_used_at` | DateTimeField, null | populated on every successful authentication |
| `last_used_ip` | GenericIPAddressField, null | resolved via django-ipware |
| `created`, `updated` | auto | |

Admin actions: **Rotate selected API keys** (replaces the raw value
+ blanks the hash for re-hashing on next save), **Revoke selected**
(toggles `is_active=False`).

## Files

### `MailFile`

Attachment for `MailTemplate`. Files are stored under `MEDIA_ROOT`
via Django's `FileField`.

| Field | Type | Notes |
|---|---|---|
| `template` | FK(`MailTemplate`) | cascade |
| `name` | CharField(100) | display |
| `filename` | FileField(upload_to=`UPLOAD_TO`) | |

## Natural keys

Seven models ship a `NaturalKeyManager` and implement `natural_key()`:
`MailCategory`, `MailBaseTemplate`, `MailFromEmail`, `MailBcc`,
`MailTemplate`, `MailLogException`, and `MailGroup`.

This enables portable fixture exports that reference objects by a
human-readable key instead of an auto-generated integer primary key:

```bash
python manage.py dumpdata dbmail \
    --natural-foreign \
    --natural-primary \
    --indent 2 \
    > fixtures/dbmail_templates.json
```

The resulting fixture can be loaded into any environment (staging,
CI database, fresh production instance) without PK conflicts:

```bash
python manage.py loaddata fixtures/dbmail_templates.json
```

The natural key for each model is its unique human-readable field
(e.g. `slug` for `MailTemplate` and `MailGroup`, `name` for
`MailCategory`).

## Cross-references

- [Settings reference](../app_settings.md) for every `DB_MAILER_*`.
- [Public API endpoint](../api.md).
- [Security model](../explanation/security.md) for hashing, plaintext caveats,
  pickle gating, EOL providers.
- [MIGRATION.md](../../MIGRATION.md) for schema highlights and
  upgrade contract (clean break — no automated 2.x → 3.0 path).
