# Sign API requests with HMAC

The public `dbmail/api/` endpoint accepts an optional HMAC body
signature. Once `DB_MAILER_API_HMAC_SECRET` is set, every request
without a valid `X-Dbmail-Signature` header returns `403 Forbidden`.
Use this when the network between the client and the dbmail host is
not fully trusted.

## 1. Configure

```python
# settings.py
DB_MAILER_API_HMAC_SECRET = "set this to 32 random bytes via env"
```

Generate via `secrets.token_urlsafe(32)`. Pass through env vars in
production:

```python
import os
DB_MAILER_API_HMAC_SECRET = os.environ["DBMAIL_API_HMAC_SECRET"]
```

## 2. Sign the request

The body to sign is the **raw form-encoded request body** (not URL).
Use SHA-256, HMAC, hex encoding, prefix with `sha256=`.

### curl + openssl

```bash
SECRET="..."
BODY='api_key=YOUR_32_CHAR_KEY&slug=welcome&recipient=user@example.com'
SIG=$(printf '%s' "$BODY" | openssl dgst -sha256 -hmac "$SECRET" -hex | awk '{print $2}')

curl -X POST http://localhost:8000/dbmail/api/ \
     -H "X-Dbmail-Signature: sha256=$SIG" \
     --data "$BODY"
```

### Python

```python
import hashlib
import hmac
import requests

SECRET = b"..."
KEY = "YOUR_32_CHAR_KEY_HERE_..............."
body = f"api_key={KEY}&slug=welcome&recipient=user@example.com"

sig = hmac.new(SECRET, body.encode(), hashlib.sha256).hexdigest()

r = requests.post(
    "http://localhost:8000/dbmail/api/",
    data=body,
    headers={
        "Content-Type": "application/x-www-form-urlencoded",
        "X-Dbmail-Signature": f"sha256={sig}",
    },
    timeout=10,
)
r.raise_for_status()
```

### Node.js

```javascript
const crypto = require("crypto");

const SECRET = process.env.DBMAIL_HMAC_SECRET;
const body = "api_key=YOUR_32_CHAR_KEY&slug=welcome&recipient=user@example.com";
const sig = crypto.createHmac("sha256", SECRET).update(body).digest("hex");

const res = await fetch("http://localhost:8000/dbmail/api/", {
  method: "POST",
  headers: {
    "Content-Type": "application/x-www-form-urlencoded",
    "X-Dbmail-Signature": `sha256=${sig}`,
  },
  body,
});
```

### Go

```go
import (
    "crypto/hmac"
    "crypto/sha256"
    "encoding/hex"
)

body := "api_key=YOUR_32_CHAR_KEY&slug=welcome&recipient=user@example.com"
mac := hmac.New(sha256.New, []byte(secret))
mac.Write([]byte(body))
sig := hex.EncodeToString(mac.Sum(nil))

req.Header.Set("X-Dbmail-Signature", "sha256="+sig)
```

## 3. Verify behaviour

```bash
# Invalid signature → 403
curl -X POST http://localhost:8000/dbmail/api/ \
     -H "X-Dbmail-Signature: sha256=deadbeef" \
     --data "$BODY"
# HTTP/1.1 403 Forbidden

# Missing header → 403 (only when secret configured)
curl -X POST http://localhost:8000/dbmail/api/ --data "$BODY"
# HTTP/1.1 403 Forbidden
```

## 4. Pitfalls

- The signature covers the **raw body** (form-encoded). Do not pass a
  parsed dict and re-serialise — Python's `requests` re-orders keys.
  Build the body string explicitly and pass it as `data=body` with
  the Content-Type header.
- The body is read once via `request.body` *before* any subsequent
  `request.POST` access — `dbmail/views.py` makes that read explicit.
- The comparison uses `hmac.compare_digest` — constant-time, immune
  to byte-level timing oracles.
- Algorithm is hard-coded to SHA-256. The header value must literally
  start with `sha256=`.
- Secret is read from `settings` on every request — rotate by
  redeploy / SIGHUP. There is no live-reload yet (3.1 follow-up).

## See also

- [api.md](../api.md) — full endpoint reference.
- [Security model](../explanation/security.md) — full security model + known
  limitations.
