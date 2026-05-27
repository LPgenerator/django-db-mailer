# Add a custom provider

You need to deliver via a vendor that `dbmail` does not bundle (e.g.
Postmark transactional, Mailgun, Vonage TTS, an internal SMTP relay).
A "provider" is a small Python module that implements `send(...)` and
is selected by passing `provider="dotted.path"` to `send_db_mail` /
`send_db_sms` / etc. — or wired in globally via `DB_MAILER_*_PROVIDER`
settings.

## Provider contract

For **mail backends** the provider is called with the live `Sender`
instance (it has `_recipient_list`, `_subject`, `_message`, `_kwargs`,
`_template`, `_from_email`, `_cc`, `_bcc`):

```python
# myapp/providers/postmark/mail.py
from django.conf import settings


class PostmarkError(Exception):
    pass


def send(sender_instance) -> bool:
    """Deliver `sender_instance._message` via the Postmark API."""
    from postmarker.core import PostmarkClient   # SDK is opt-in

    client = PostmarkClient(server_token=settings.POSTMARK_TOKEN)
    response = client.emails.send(
        From=sender_instance._from_email,
        To=", ".join(sender_instance._recipient_list),
        Subject=sender_instance._subject,
        HtmlBody=sender_instance._message if sender_instance._template.is_html else None,
        TextBody=None if sender_instance._template.is_html else sender_instance._message,
        Cc=", ".join(sender_instance._cc) if sender_instance._cc else None,
        Bcc=", ".join(sender_instance._bcc) if sender_instance._bcc else None,
    )
    if response.get("ErrorCode", 0) != 0:
        raise PostmarkError(response.get("Message", "unknown"))
    return True
```

For **sms / push / tts / bot backends** the contract is simpler:

```python
# myapp/providers/postmark/push.py
def send(recipient: str, message: str, **kwargs) -> bool:
    """``recipient`` is a single token; iterate inside if needed."""
    ...
```

## Wire in

### Per-call

```python
from dbmail import send_db_mail

send_db_mail(
    "welcome",
    "user@example.com",
    {"user": "Alice"},
    provider="myapp.providers.postmark.mail",
)
```

> **Security note** — the public HTTP API endpoint (`dbmail/api/`)
> rejects an attacker-supplied `provider` field by default. To allow
> client-driven provider selection, set both
> `DB_MAILER_API_ALLOW_PROVIDER_OVERRIDE = True` and an exhaustive
> `DB_MAILER_API_PROVIDER_ALLOWLIST = (...)`. See the
> [security model](../explanation/security.md).

### Project-wide default

```python
# settings.py
DB_MAILER_MAIL_PROVIDER = "myapp.providers.postmark.mail"
DB_MAILER_PUSH_PROVIDER = "myapp.providers.postmark.push"
DB_MAILER_SMS_PROVIDER = "myapp.providers.smsaero.sms"   # bundled
```

The Sender reads these at import time. Restart workers after edit.

## Lazy SDK import

**Never import the SDK at module level** — it must live inside `send()`:

```python
# Good
def send(sender_instance):
    from postmarker.core import PostmarkClient   # ← deferred
    client = PostmarkClient(...)
    ...

# Bad — `import dbmail.providers.myapp.postmark.mail` blows up if
# postmarker is not installed.
from postmarker.core import PostmarkClient
```

The `dbmail.providers.pubnub.push` module follows this pattern and
emits a `PubNubError("install via pip install ...[pubnub]")` if the
SDK is missing.

## Required settings

Document the `settings.py` keys your provider reads in your project's
deployment runbook. `dbmail` has no opinion — `settings.POSTMARK_TOKEN`
or `settings.MYAPP_PROVIDER_KEY`, your call.

## Testing

```python
# tests/test_postmark_provider.py
from unittest.mock import MagicMock, patch
import pytest


def test_postmark_send_success():
    from myapp.providers.postmark import mail

    sender = MagicMock(
        _recipient_list=["a@example.com"],
        _from_email="me@example.com",
        _subject="Hi",
        _message="<p>Hi</p>",
        _template=MagicMock(is_html=True),
        _cc=[], _bcc=[],
    )

    fake_client = MagicMock()
    fake_client.emails.send.return_value = {"ErrorCode": 0}

    with patch("postmarker.core.PostmarkClient", return_value=fake_client):
        assert mail.send(sender) is True

    assert fake_client.emails.send.called


def test_postmark_send_error_raises():
    from myapp.providers.postmark import mail

    sender = MagicMock(_template=MagicMock(is_html=True), _cc=[], _bcc=[])
    sender._recipient_list = ["a@example.com"]

    fake_client = MagicMock()
    fake_client.emails.send.return_value = {"ErrorCode": 422, "Message": "bad"}

    with patch("postmarker.core.PostmarkClient", return_value=fake_client):
        with pytest.raises(mail.PostmarkError, match="bad"):
            mail.send(sender)
```

Use `responses` / `respx` for HTTP-based providers; mock the SDK
client class for SDK-based providers (telegram, sendinblue, pubnub).

## See also

- [reference/models.md](../reference/models.md#mailtemplate) — what
  fields are accessible on `sender_instance._template`.
- [custom_backends_and_providers.md](../custom_backends_and_providers.md) — full
  backend (Sender) extension guide if you need to override more than
  the provider.
- [providers.md](../providers.md) — list of bundled providers.
