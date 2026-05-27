# Подписать API-запросы через HMAC

Публичный endpoint `dbmail/api/` поддерживает опциональную HMAC-
подпись тела запроса. Как только установлен
`DB_MAILER_API_HMAC_SECRET`, любой запрос без корректного заголовка
`X-Dbmail-Signature` возвращает `403 Forbidden`. Используйте, когда
сеть между клиентом и dbmail-хостом не полностью доверена.

## 1. Настроить

```python
# settings.py
DB_MAILER_API_HMAC_SECRET = "случайные 32 байта через переменную окружения"
```

Сгенерируйте через `secrets.token_urlsafe(32)`. В production
получайте через env var:

```python
import os
DB_MAILER_API_HMAC_SECRET = os.environ["DBMAIL_API_HMAC_SECRET"]
```

## 2. Подписать запрос

Подписывается **сырое form-encoded тело запроса** (не URL).
Алгоритм SHA-256, HMAC, hex, префикс `sha256=`.

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

## 3. Проверить поведение

```bash
# Невалидная подпись → 403
curl -X POST http://localhost:8000/dbmail/api/ \
     -H "X-Dbmail-Signature: sha256=deadbeef" \
     --data "$BODY"
# HTTP/1.1 403 Forbidden

# Заголовок отсутствует → 403 (только когда secret настроен)
curl -X POST http://localhost:8000/dbmail/api/ --data "$BODY"
# HTTP/1.1 403 Forbidden
```

## 4. Подводные камни

- Подпись охватывает **сырое тело** (form-encoded). Не передавайте
  словарь и не сериализуйте заново — `requests` в Python переставит
  ключи. Соберите строку тела явно и передайте как `data=body` с
  заголовком Content-Type.
- Тело читается через `request.body` **до** любого последующего
  обращения к `request.POST` — `dbmail/views.py` делает это явно.
- Сравнение через `hmac.compare_digest` — постоянное время,
  иммунно к timing-oracle.
- Алгоритм жёстко SHA-256. Заголовок должен начинаться буквально с
  `sha256=`.
- Secret читается из `settings` на каждый запрос — ротируйте через
  redeploy / SIGHUP. Live-reload пока нет (3.1 follow-up).
