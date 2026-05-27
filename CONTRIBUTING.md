# Contributing

Contributions are welcome. Every bit helps.

## Requirements

- Python 3.10–3.14
- Django 4.2 LTS, 5.2 LTS, or 6.0
- [Git](https://git-scm.com/)

## Development setup

```bash
git clone https://github.com/LPgenerator/django-db-mailer.git
cd django-db-mailer
python -m venv .venv
source .venv/bin/activate
make install-dev   # pip install -e ".[dev,test,demo]"
```

## Running checks

```bash
make lint          # ruff + flake8 + mypy — must be green before every commit
make test          # pytest against the active Python/Django combination
make coverage      # pytest + diff-cover — new code requires 100% branch coverage
make security      # bandit + semgrep + pip-audit
```

All four commands must pass before you open a pull request.

## Running against the full matrix

The CI matrix covers Python 3.10–3.14 × Django 4.2/5.2/6.0. To reproduce
locally:

```bash
pip install tox
tox
```

## Making changes

1. Fork the repository and create a branch from `master`.
2. Write tests for every change — new code must have 100% branch coverage
   (`diff-cover` enforces this in CI).
3. Run `make lint` and `make test`. Fix any failures before pushing.
4. Open a pull request against `master`. Describe what changed and why.

## Reporting bugs

Open an issue at <https://github.com/LPgenerator/django-db-mailer/issues>.
Include:

- Python and Django versions.
- A minimal reproduction case.
- Full traceback if applicable.

## Pull request checklist

- [ ] `make lint` passes (ruff, flake8, mypy).
- [ ] `make test` passes on Python 3.11+ / Django 4.2+.
- [ ] `make coverage` shows no uncovered new lines (`diff-cover` threshold: 100%).
- [ ] `CHANGELOG.md` updated under `[Unreleased]`.
- [ ] No secrets, tokens, or personal paths in any committed file.

## Code style

- PEP 8. `ruff` is the formatter and linter — run `make lint-fix` to
  auto-correct formatting issues.
- Type hints on all public functions. `mypy` runs in strict mode.
- `from __future__ import annotations` at the top of every new file.
- Log via `logging.getLogger(__name__)` — no `print()`.
- Catch specific exceptions, not bare `except Exception`.

## Provider contributions

New providers go in `dbmail/providers/<name>/`. The `send()` function must:

- Import the vendor SDK inside `send()`, not at module level.
- Use `requests.Session` or `httpx.Client` with `timeout=10`.
- Never log `api_key`, `token`, or `password` values.
- Include a test in `tests/providers/` using `responses` or `unittest.mock`.

See `docs/how_to/add_custom_provider.md` for the full contract.

## License

By contributing you agree that your work will be released under the
[MIT License](LICENSE).
