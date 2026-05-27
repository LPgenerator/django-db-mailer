# HTTP API reference

`dbmail` exposes a single HTTP endpoint that lets external services
trigger email/SMS/push/TTS/bot sends without importing Python.

## Mount the endpoint

```python
# urls.py
from django.urls import include, path

urlpatterns = [
    path("dbmail/", include("dbmail.urls", namespace="dbmail")),
]
```

The send endpoint is available at `POST /dbmail/api/`.

## Authentication

Every request must supply a valid `ApiKey`. Pass it in one of two ways:

- **Form field** — `api_key=<raw-value>` in the POST body.
- **HTTP header** — `Authorization: ApiKey <raw-value>`.

The raw value is matched against the stored Argon2/PBKDF2 hash. The
plain `api_key` column is kept for 3.x read-back only and will be
removed in 4.0.

Manage keys at `/admin/dbmail/apikey/`. See
[how_to/rotate_apikey.md](how_to/rotate_apikey.md) for rotation
procedures.

## Request fields

| Field | Required | Description |
|---|---|---|
| `api_key` | yes* | Raw API key (or use `Authorization` header). |
| `slug` | yes | `MailTemplate.slug` to render and send. |
| `recipient` | yes | Email address, phone number, push token, or `MailGroup.slug`. |
| `from_email` | no | Override the template's `From:` address. |
| `subject` | no | Override the template subject line. |
| `use_celery` | no | `1` to dispatch via Celery (default: `0`, synchronous). |
| `provider` | no | Dotted import path to a custom provider (blocked by default — see security note below). |
| `correlation_id` | no | Business correlation key (order ID, request ID, trace ID) stored on the resulting `MailLog` row. Max 64 characters. |

\* Required unless sent via `Authorization` header.

## Responses

| Status | Meaning |
|---|---|
| `200 OK` | Send dispatched (or queued to Celery). Body: `{"result": "ok"}`. |
| `400 Bad Request` | Missing required field or template inactive. Body: `{"error": "<reason>"}`. |
| `401 Unauthorized` | Missing or invalid API key. Body: `{"error": "Unauthorized"}`. |
| `403 Forbidden` | API endpoint disabled via `DB_MAILER_API_DISABLE = True`. Body: `{"error": "Forbidden"}`. |
| `429 Too Many Requests` | Rate limit exceeded. Body: `{"error": "Too Many Requests"}`. |

## curl example

```bash
curl -X POST https://yourapp.example.com/dbmail/api/ \
  -d "api_key=YOUR32CHARKEY" \
  -d "slug=welcome" \
  -d "recipient=user@example.com"
```

With `Authorization` header:

```bash
curl -X POST https://yourapp.example.com/dbmail/api/ \
  -H "Authorization: ApiKey YOUR32CHARKEY" \
  -d "slug=welcome" \
  -d "recipient=user@example.com"
```

## Python example

```python
import httpx

response = httpx.post(
    "https://yourapp.example.com/dbmail/api/",
    data={
        "api_key": "YOUR32CHARKEY",
        "slug": "welcome",
        "recipient": "user@example.com",
        "correlation_id": "order-12345",
    },
    timeout=10,
)
response.raise_for_status()
print(response.json())   # {"result": "ok"}
```

`correlation_id` is stored on the `MailLog` row so you can look up
every message related to a specific order or request without scanning
the full log table. Pass an OpenTelemetry trace ID to link dbmail
sends to your distributed traces.

## HMAC body signature (optional)

Enable request-body integrity verification:

```python
# settings.py
DB_MAILER_API_HMAC_SECRET = "your-shared-secret"
```

Sign the POST body with HMAC-SHA-256 and send the hex digest in the
`X-DBMail-Signature` header. Requests without a valid signature are
rejected with `403`. See
[how_to/api_with_hmac.md](how_to/api_with_hmac.md) for the signing
algorithm and a complete example.

## Rate limiting

```python
# settings.py
DB_MAILER_API_RATE_LIMIT = "60/m"   # 60 requests per minute per API key
```

Exceeded requests return `429`. Set to `None` (default) to disable.

## Kill switch

```python
# settings.py
DB_MAILER_API_DISABLE = True
```

All requests return `403` immediately. Use to block the endpoint without
undeploying.

## Provider override security

By default the `provider` field is silently ignored to prevent callers
from loading arbitrary Python modules. To allow it:

```python
DB_MAILER_API_ALLOW_PROVIDER_OVERRIDE = True
DB_MAILER_API_PROVIDER_ALLOWLIST = (
    "myapp.providers.postmark.mail",
    "myapp.providers.mailgun.mail",
)
```

Requests supplying a `provider` value not in the allowlist are rejected
with `400`.

## See also

- [reference/models.md](reference/models.md#api) — `ApiKey` field list.
- [how_to/rotate_apikey.md](how_to/rotate_apikey.md) — key rotation.
- [how_to/api_with_hmac.md](how_to/api_with_hmac.md) — HMAC signing.
- [explanation/security.md](explanation/security.md) — full threat model.
