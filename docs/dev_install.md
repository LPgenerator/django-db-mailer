# Development install

## Prerequisites

- Python ≥ 3.10 (3.10–3.14 supported, see `tox.ini`)
- PostgreSQL (or Docker — see below)
- Redis (or Docker)
- `gettext` if you plan to touch translations

```bash
# macOS
brew install python@3.13 redis postgresql@16 gettext

# Debian / Ubuntu
sudo apt-get install -y python3-dev redis-server postgresql gettext libxml2-dev libxslt-dev zlib1g-dev
```

## Clone + install

```bash
git clone --depth 1 https://github.com/LPgenerator/django-db-mailer.git
cd django-db-mailer

python3 -m venv .venv
source .venv/bin/activate

pip install -e ".[dev,test,demo,docs,celery]"
```

`pip install -e .` is the canonical editable install; the legacy
`python setup.py develop` was removed when the project switched to
`pyproject.toml` build backend in 3.0.

## Run the demo

```bash
cd demo
python manage.py migrate --noinput
DJANGO_SUPERUSER_PASSWORD=admin python manage.py createsuperuser \
    --username admin --email admin@example.com --noinput

# Terminal 1 — Redis
redis-server

# Terminal 2 — Django dev server
python manage.py runserver

# Terminal 3 — Celery worker
celery -A demo worker -l INFO -Q default

# Terminal 4 — Django shell
python manage.py shell_plus --print-sql
```

Or with Docker Compose (faster, single command):

```bash
docker compose up -d --wait
# admin auto-bootstraps; visit http://localhost:8000/admin/login/
# default credentials: admin / admin
```

## Smoke shell session

```python
from dbmail.models import MailTemplate, MailGroup, MailGroupEmail, MailLog, MailFromEmail
from dbmail import send_db_mail

sender = MailFromEmail.objects.create(name="from", email="from@example.com")
MailTemplate.objects.create(
    name="Site welcome template",
    subject="Welcome",
    message="Welcome to our site. We are glad to see you.",
    slug="welcome",
    is_html=False,
    from_email=sender,
)

group = MailGroup.objects.create(name="Site admins", slug="administrators")
MailGroupEmail.objects.bulk_create([
    MailGroupEmail(name="Admin 1", email="admin1@example.com", group=group),
    MailGroupEmail(name="Admin 2", email="admin2@example.com", group=group),
])

# Single recipient
send_db_mail("welcome", "you@example.com", use_celery=False)

# List of recipients
send_db_mail("welcome", ["a@example.com", "b@example.com"], use_celery=False)

# Internal group
send_db_mail("welcome", "administrators", use_celery=False)

# Inspect log
print(MailLog.objects.count())
```

## Make targets

```bash
make help              # list every target with its description

# Linting / formatting
make lint              # ruff + flake8
make lint-fix          # ruff format + ruff check --fix
make typecheck         # mypy on dbmail/

# Tests
make test              # pytest
make coverage          # pytest --cov + html report
make tox               # full Python × Django matrix

# Security
make security          # bandit + pip-audit

# Build / release (maintainer)
make build             # python -m build (wheel + sdist)
make smoke-install     # build + install into a fresh venv
make release-test      # twine upload --repository testpypi
make check             # everything in one shot

# Demo
make demo-migrate      # apply demo migrations
make demo-run          # runserver
make demo-worker       # celery worker

# Translations
make messages          # django-admin makemessages -l ru
make compilemessages   # django-admin compilemessages

# Docs (Sphinx)
make docs              # sphinx-build with -W
make docs-serve        # local preview
```

## Running the test suite

Single python / Django combination:

```bash
pytest tests/ -v
pytest tests/test_admin_integration.py::TestApiKeyAdmin -v
```

Full matrix (slow on cold cache):

```bash
tox -p auto
```

The matrix is `py3.10..3.14` × `django4.2/5.2/6.0` per `tox.ini`.

## Translation workflow

```bash
# Inside dbmail/, regenerate .po after touching gettext_lazy strings
cd dbmail
django-admin makemessages -l ru --no-obsolete

# Translate empty msgstr in dbmail/locale/ru/LC_MESSAGES/django.po,
# then compile:
django-admin compilemessages -l ru
```

`compilemessages` writes the `.mo` file. The package ships with the
`.mo` so end-user installs do not need `gettext` at runtime.

## Pre-commit

```bash
pre-commit install
pre-commit run --all-files
```

Hooks: `ruff-check`, `ruff-format`, `trailing-whitespace`,
`end-of-file-fixer`, `markdownlint` (when present).
