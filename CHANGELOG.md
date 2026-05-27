# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).
See [VERSIONS.md](VERSIONS.md) for the public versioning policy.

## [Unreleased]

## [3.0.0rc2] — 2026-05-02

Release candidate cut for the `3.0.0` modernization sweep. Tag and
PyPI publication of `3.0.0` follows after a 2-3 week feedback window
on TestPyPI per the release plan.

## [3.0.0] — 2026-XX-XX

> **Major release.** Full modernization of the package, the demo project,
> packaging, tests, CI/CD and deployment story. **The migration history
> has been wiped** — see [MIGRATION.md](MIGRATION.md) for the supported
> upgrade procedure for installations on `2.x`.

### Added

- `MailLog.correlation_id` — optional CharField(64, db_index, null) for
  business-level correlation (order ID, request ID, OpenTelemetry trace ID).
  Pass as `correlation_id=` kwarg to any `send_db_*` function or as a POST
  field to `/dbmail/api/`. Visible in `MailLogAdmin` list and search. Migration 0003.
- `DB_MAILER_USE_JINJA2_SANDBOX` (bool, default `False`) — opt-in sandboxed
  Jinja2 renderer for `MailTemplate` bodies and subjects. Blocks
  `__class__.__init__.__globals__` gadget chains. Requires
  `pip install django-db-mailer[sandbox]` (Jinja2 >= 3.1). Django-specific
  template tags (`{% load %}`, `{% url %}`) are unavailable in sandbox mode.
- `DB_MAILER_SIGNAL_CHOICES` — configurable sequence of
  `(dotted_path, label)` tuples that populate the `Signal.signal` dropdown.
  Default covers `post_save`, `pre_save`, `post_delete`, `pre_delete`,
  `m2m_changed`. Extend with custom application signals by setting
  `DB_MAILER_SIGNAL_CHOICES` in `settings.py`. Migration 0005 contains a
  forward+reverse data migration mapping legacy short names to dotted paths.
- `ApiKeyUsageAudit` model — persistent audit log for every hit on
  `/dbmail/api/`. Records `action`, `success`, `ip`, `ua`, `detail`, and
  FK to `ApiKey`. Admin view is read-only. Migration 0006.
- `NaturalKeyManager` on seven models (`MailCategory`, `MailBaseTemplate`,
  `MailFromEmail`, `MailBcc`, `MailTemplate`, `MailLogException`, `MailGroup`).
  Enables `dumpdata --natural-foreign --natural-primary` / `loaddata`
  portable fixture workflows between environments.
- Python 3.10 – 3.14 supported. Django 4.2 LTS / 5.2 LTS / 6.0 supported.
- Modern packaging via `pyproject.toml` (PEP 517/621), single source of
  truth for metadata.
- Optional dependency groups for every shipped provider: `[apns]`,
  `[fcm]`, `[twilio]`, `[pubnub]`, `[vonage]`, `[brevo]`, plus
  `[all-providers]` meta-extra.
- API endpoint security hardening:
  - `ApiKey.password_hash` (Argon2 / PBKDF2 via Django hashers).
    Plain-text `api_key` column is kept until 4.0 for backwards
    compatibility.
  - Cache-based per-key rate limit, configurable via
    `DB_MAILER_API_RATE_LIMIT = (count, seconds)` (default `(60, 60)`).
  - Optional HMAC-SHA-256 body signature, enabled via
    `DB_MAILER_API_HMAC_SECRET`.
  - `ApiKey.last_used_at` and `ApiKey.last_used_ip` columns for
    operational visibility.
- Path-traversal hardening for `SafariPushPackagesView`.
- SSRF hardening for `dbmail.providers.http.push`: `https://` only by
  default, optional host allowlist via `DBMAIL_HTTP_ALLOWED_HOSTS`,
  DNS-resolution check for RFC1918 / link-local / loopback / CGNAT /
  ULA destinations.
- `SignalDeferredDispatch` now supports JSONField storage for
  `args` / `kwargs` / `params`. Dual-write with pickle fallback;
  pickle path is removed in 4.0.
- Multi-stage Dockerfile (`builder` / `base` / `development` /
  `production`) with non-root user, HEALTHCHECK, tini.
- `docker-compose.yml` with postgres, redis, web, celery-worker, celery-beat
  (under `beat` profile), healthchecks, security_opt, 127.0.0.1 bind.
- GitHub Actions CI: lint / test (5-cell matrix Python × Django) /
  wheel-smoke / diff-cover. Release pipeline with PyPI trusted
  publishing, PEP 740 attestations, sigstore signing, CycloneDX SBOM.
  Security pipeline: pip-audit, semgrep, gitleaks, trivy. CodeQL.
- pytest test suite with 102 tests covering the new code paths
  (ApiKey security, JSON dual-write, rate limit, HMAC, path traversal,
  SSRF, EOL deprecation warnings, migrations forward+reverse,
  Celery task wiring). Coverage baseline: 44%, ratchet plan
  40 → 60 → 75 → 85 → 95 across 3.0 → 3.4 minor releases.
- `MIGRATION.md` with the supported upgrade procedure from 2.x.

### Changed

- `Signal.signal` field `max_length` increased from 15 to 255 to accommodate
  dotted-path module references (e.g. `myapp.signals.order_paid`). Migration 0005
  rewrites existing short-name values (`post_save` → `django.db.models.signals.post_save`)
  and is fully reversible.
- Minimum Python: **3.10** (was 3.6 in 2.5.x).
- Minimum Django: **4.2 LTS** (was 1.11 in 2.5.x).
- Build backend: `setuptools >= 68` via `pyproject.toml` (was
  legacy `setup.py`).
- `dbmail/__init__.py`: introduces `__version__: str` (canonical).
  Legacy `VERSION = (3, 0, 0)` tuple is preserved for back-compat.
- All Python 2 era compatibility shims removed (`PY3`, `PY2`,
  `python_2_unicode_compatible`, `class X(object):`, `# coding=utf-8;`
  headers, `from __future__ import unicode_literals/division/print_function`).
- All deprecated Django APIs removed: `ugettext_lazy` →
  `gettext_lazy`, `from django.conf.urls import url` →
  `re_path`/`path`, `from django.utils.importlib import import_module`
  → `from importlib import import_module`, `default_app_config`
  removed (Django ≥ 3.2 picks up AppConfig automatically),
  `_meta.module_name` → `_meta.model_name`, `index_together` →
  `Meta.indexes`.
- All providers' SDK imports moved inside `send()` so importing the
  provider module on a fresh venv works without the optional SDK
  installed.
- `apple/apns.py` rewritten for Python 3.12+ compatibility
  (`ssl.create_default_context()` instead of the removed
  `socket.ssl` / module-level `ssl.wrap_socket`).
- `apple/apns2.py` rewritten on `httpx[http2]` (the legacy `hyper`
  package has been unmaintained since 2020 and does not install
  on modern Python).
- Demo project adapted, not stripped: Grappelli upgraded to 4.x,
  CKEditor to 6.x, Reversion to 5.x, all gated by `_add_if_installed`
  helpers in `demo/demo/settings.py`.
- Database PKs are `BigAutoField` by default.
- `dbmail.providers._compat` is the new home of the shared
  `from_unicode` helper. The legacy import path
  `dbmail.providers.prowl.push.from_unicode` still works but emits
  `DeprecationWarning`.

### Deprecated

- The plain `ApiKey.api_key` column will be removed in 4.0. Operators
  should rely on `password_hash` from now on.
- `SignalDeferredDispatch.args` / `kwargs` / `params` (TextField pickle
  blobs) will be removed in 4.0 in favour of `*_json` JSONField columns.
- `dbmail.providers.parse_com` — Parse.com was shut down on 2017-01-28.
  Module emits `DeprecationWarning` on `send()`. Will be removed in 4.0.
- `dbmail.providers.boxcar` — Boxcar service has been EOL since ~2016.
  Same.
- `dbmail.providers.prowl` — Prowl has been EOL since ~2020. Same.
- `dbmail.providers.apple.apns` (binary protocol) — Apple shut down
  the protocol on 2021-06. Use `dbmail.providers.apple.apns2` instead.
- Python 3.10 — supported in 3.0.0 only; will be dropped in 3.1.0
  after the upstream CPython EOL in October 2026.

### Removed

- Python ≤ 3.9 support.
- Django ≤ 4.1 support.
- The `dbmail.import_module()` py2/py3 compat wrapper (use
  `from importlib import import_module`).
- `setup.py`, `setup.cfg`, `.travis.yml`, `.travis.yml.log`,
  `.landscape.yaml`.
- `dbmail/test_cases.py` (legacy `manage.py test` test cases —
  contents reimplemented in `tests/`).
- All 17 legacy migrations `0001..0017`. **Replaced by a single
  `0001_initial.py` reflecting the final 3.0 schema and a
  `0002_apikey_hash_data.py` data migration. See MIGRATION.md.**

### Fixed

- `MailSubscriptionAbstract.notify` no longer raises `KeyError` when a
  subscriber record is missing a backend key, and no longer generates N+1
  queries on group recipient resolution.
- `ApiKey.clean_cache` no longer loads all cache keys into memory (OOM on
  large installations); now uses targeted key invalidation.
- `Signal.mark_as_sent` is now idempotent under Celery worker races.
  A `UniqueConstraint` on `(model, model_pk, signal)` in `SignalLog` prevents
  duplicate sends when two workers process the same signal event concurrently.
  Migration 0004.
- `MailTemplateAdmin.get_queryset` now uses `select_related` to eliminate N+1
  queries on the template list page.
- `dbmail/views.py:send_by_dbmail` no longer raises
  `RawPostDataException` when HMAC verification is enabled
  (`request.body` was being accessed after `request.POST` had
  consumed the input stream).
- `dbmail/providers/apple/apns.py` no longer fails to import on
  Python 3.12+ (`from socket import ssl` was removed in 3.12;
  rewritten using `ssl.create_default_context()`).
- `dbmail/providers/apple/apns2.py` no longer depends on the dead
  `hyper` package.
- `dbmail/providers/centrifugo/push.py` and
  `dbmail/providers/pushall/push.py` no longer use `urllib2`.
- `dbmail/providers/telegram/bot.py` no longer fails to import on
  fresh venvs (was importing `telepot` at module level) and no longer
  raises `AttributeError` on `kwargs.iteritems()` (Python 2 method).
- `dbmail/backends/mail.py` no longer imports `distutils.version`,
  removed in Python 3.12.
- `demo/demo/celery.py` was shipping with `Celery("config")` instead
  of `Celery("demo")`, which prevented `autodiscover_tasks` from
  finding dbmail tasks.

### Security

- **SEC-1 (CWE-94/CWE-470)** — `dbmail/views.py` no longer accepts
  `provider` from the public API request. Any holder of a valid
  `ApiKey.api_key` could previously POST a dotted-path module name
  that the Sender backend would feed into `importlib.import_module`,
  escalating an authenticated key into post-auth RCE. The field is
  now opt-in via `DB_MAILER_API_ALLOW_PROVIDER_OVERRIDE = True` and
  must additionally pass an exhaustive
  `DB_MAILER_API_PROVIDER_ALLOWLIST` tuple. CVSS estimate ~9.1
  (network / low complexity / authenticated).
- **SEC-2 (CWE-1336 SSTI)** — `MailTemplate.subject`, `MailTemplate.message`,
  `MailBaseTemplate.message`, and `Signal.rules` are rendered through
  Django's `Template().render(Context())` against the model instance
  that fired the dispatch. Any non-superuser staff with
  `dbmail.change_mailtemplate` / `change_signal` could otherwise
  paste a context-walking gadget chain to read settings or
  environment. The four fields are now read-only for users that lack
  `is_superuser`, the explicit `dbmail.edit_template_body`, or
  `dbmail.edit_signal_rules` permission. Sandboxed Jinja2 renderer
  ships in 3.1.
- **SEC-7** — `dbmail.providers.smsaero.sms` upgraded from
  `HTTPConnection` to `HTTPSConnection`. The vendor supports HTTPS;
  the plain-HTTP request body included basic-auth credentials in the
  query string and was a CWE-319 leak surface. Operators with
  customised `api_url` should verify HTTPS reachability.
- **`DB_MAILER_API_DISABLE`** kill-switch — operators can now disable
  the public `dbmail/api/` endpoint without restarting Celery
  workers. Useful during incident response.
- The 2.4.x line is frozen and receives no further releases. Stay on
  it only if you cannot move past Python ≤ 3.9 / Django ≤ 4.1.

### Known operational gaps (planned for the 3.x cycle)

3.0.0 is shippable to production with operator effort, but it is not
yet a "highload by default" release. The following items are tracked
explicitly so operators size their deployment correctly:

- **N+1 on `MailLog.store`** — every recipient is a separate
  `MailLogEmail.objects.create()`. At ≥ 10 k msgs/day this is a
  measurable DB-RTT cost. `bulk_create` + `transaction.atomic` ships
  in `3.0.1`.
- **No shared HTTP client across providers** — every push/SMS opens
  a fresh TCP+TLS handshake. Timeouts are now in place on 14
  providers, but `requests.Session()` + `urllib3.util.Retry` with
  status-forced retries (`429/502/503/504`) is `3.1`. (PERF-3.)
- **No `X-Request-ID` correlation** — the package does not stamp a
  request id on outbound provider calls or Celery payloads. Wire it
  in your project middleware until `3.1`.
- **No Prometheus metrics, no Sentry hook, no circuit breaker**.
  Operate via Celery's own metrics + your APM. The bundled
  `dbmail.contrib.metrics` ships in `3.1`. (PERF-19, PERF-21.)
- **SMTP password is plaintext at rest** — `MailFromEmailCredential.password`
  stored as plain text; encrypted column lands in `3.1`. See
  [docs/explanation/security.md](docs/explanation/security.md).
- **EOL providers (`parse_com`, `boxcar`, `prowl`, `apple/apns`,
  `google/android`)** emit `DeprecationWarning` and are scheduled
  for removal in `4.0`. They keep working in `3.x` but the upstream
  service is dead — plan migration in parallel.
- **`select_for_update(skip_locked=True)` in deferred-signal cron
  needs PostgreSQL or MySQL 8** — SQLite does not honor `skip_locked`
  and will fall back to lock contention at scale. Documented for
  development environments.

## [2.5.0] — 2021-XX-XX and earlier

See git history before commit `137fce5`. Pre-3.0 changelog is not
reformatted; the 3.0 modernization is the documented baseline going
forward.

[Unreleased]: https://github.com/LPgenerator/django-db-mailer/compare/v3.0.0...HEAD
[3.0.0]: https://github.com/LPgenerator/django-db-mailer/releases/tag/v3.0.0
