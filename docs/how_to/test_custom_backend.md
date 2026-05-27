# Test a custom backend / provider

You wrote a custom Sender or provider following
[add_custom_provider.md](add_custom_provider.md). Before pushing to
production, here is how to verify it without spamming a real vendor.

## Test infrastructure

`dbmail` already ships:

- `pytest` + `pytest-django` (in `[test]` extras).
- `responses` for stubbing `requests` calls.
- `respx` for stubbing `httpx` calls (HTTP/2 — apns2).
- `pytest-mock` for `mocker.patch.object` on legacy `http.client`
  providers.
- `factory-boy` for model fixtures.
- `django-test-migrations` for migration-level tests.

Install:

```bash
pip install -e ".[test,dev]"
```

## Fixtures shared across tests

Reuse the existing project conftest via `tests/conftest.py`:

```python
@pytest.fixture
def template(db):
    from dbmail.models import MailFromEmail, MailTemplate

    sender = MailFromEmail.objects.create(name="from", email="from@example.com")
    return MailTemplate.objects.create(
        name="t", subject="hi {{user}}", slug="t-tpl",
        message="Hello {{user}}", is_html=False, from_email=sender,
    )


@pytest.fixture
def locmem_email(settings):
    settings.EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"
```

## Test pattern A — provider stubbing the SDK client

For SDK-based providers (Postmark, Brevo, Twilio):

```python
# tests/test_postmark_provider.py
from unittest.mock import MagicMock, patch

import pytest


def test_postmark_send_calls_api(template, mocker):
    from dbmail.backends.mail import Sender
    from dbmail import send_db_mail

    fake_client = MagicMock()
    fake_client.emails.send.return_value = {"ErrorCode": 0}

    with patch("postmarker.core.PostmarkClient", return_value=fake_client):
        send_db_mail(
            template.slug, "you@example.com", {"user": "Alice"},
            provider="myapp.providers.postmark.mail",
            use_celery=False,
        )

    args, kwargs = fake_client.emails.send.call_args
    assert kwargs["To"] == "you@example.com"
    assert "Alice" in kwargs["Subject"]
```

## Test pattern B — provider with `requests`

For providers that hit a vendor HTTP API directly:

```python
# tests/test_myapi_provider.py
import responses


@responses.activate
def test_myapi_send_returns_true(template):
    from myapp.providers.myapi import push
    from dbmail import send_db_push

    responses.add(
        responses.POST,
        "https://api.example.com/v1/push",
        json={"status": "ok"},
        status=200,
    )

    send_db_push(
        template.slug, "device-token-123",
        provider="myapp.providers.myapi.push",
        use_celery=False,
    )

    assert len(responses.calls) == 1
    assert "device-token-123" in responses.calls[0].request.body.decode()


@responses.activate
def test_myapi_5xx_raises(template):
    from myapp.providers.myapi import push

    responses.add(
        responses.POST,
        "https://api.example.com/v1/push",
        json={"error": "internal"},
        status=500,
    )

    with pytest.raises(push.MyApiError):
        push.send("device-token", "msg", event="test")
```

## Test pattern C — mail-backend stub

If you wrote a `Sender` subclass that overrides `_send` rather than a
provider, integrate via `EMAIL_BACKEND`:

```python
def test_locmem_outbox(template, locmem_email):
    from django.core import mail
    from dbmail import send_db_mail

    mail.outbox.clear()
    send_db_mail(template.slug, "you@example.com", {"user": "Alice"}, use_celery=False)

    msg = mail.outbox[0]
    assert msg.to == ["you@example.com"]
    assert msg.subject == "hi Alice"
    assert msg.body == "Hello Alice"
```

## Test pattern D — full provider import smoke

A "does it import?" smoke test catches regressions where a refactor
breaks `import myapp.providers.foo.mail`:

```python
import importlib
import pytest


@pytest.mark.parametrize("dotted", [
    "myapp.providers.postmark.mail",
    "myapp.providers.myapi.push",
])
def test_provider_module_imports(dotted):
    importlib.import_module(dotted)
```

The bundled providers in `dbmail.providers.*` follow the
**lazy-SDK-import** rule (SDKs imported inside `send()`, not at
module level) so the import succeeds even when the SDK is missing —
mirror that pattern in your own provider.

## Test pattern E — Celery dispatch path

```python
def test_celery_path_does_not_leak_user_instance(template, locmem_email, settings):
    settings.CELERY_TASK_ALWAYS_EAGER = True
    settings.CELERY_TASK_EAGER_PROPAGATES = True

    from django.contrib.auth import get_user_model
    from django.core import mail
    from dbmail import send_db_mail

    User = get_user_model()
    user = User.objects.create_user(username="alice", email="a@e.com")

    mail.outbox.clear()
    # use_celery=True hits apply_async; with eager mode we run inline
    # but go through the JSON serializer.
    send_db_mail(template.slug, "you@example.com", {"user": "Alice"}, use_celery=True)

    assert len(mail.outbox) == 1
```

If this raises `EncodeError: Object of type User is not JSON
serializable`, you are passing a User instance through the kwargs
pipeline. Pass `user.pk` instead of the User instance.

## CI

Wire into the existing matrix in `.github/workflows/ci.yml`:

```yaml
- name: Run provider tests
  run: pytest tests/test_*_provider.py -v
```

Or use `tox -e py313-django60 -- tests/test_*_provider.py`.

## See also

- [add_custom_provider.md](add_custom_provider.md) — the writing
  side.
- [tests/test_security_sec1_sec2.py](https://github.com/LPgenerator/django-db-mailer/blob/master/tests/test_security_sec1_sec2.py)
  — production-grade SEC regression test as a style reference.
- [tests/providers/test_http_providers.py](https://github.com/LPgenerator/django-db-mailer/blob/master/tests/providers/test_http_providers.py)
  — bundled provider tests as templates.
