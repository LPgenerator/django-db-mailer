# Makefile for django-db-mailer.
# Single source of truth for local dev commands.

PYTHON ?= python3
PIP    ?= $(PYTHON) -m pip
PYTEST ?= $(PYTHON) -m pytest

# Colours
GREEN  := \033[0;32m
YELLOW := \033[1;33m
RED    := \033[0;31m
CYAN   := \033[0;36m
NC     := \033[0m

.DEFAULT_GOAL := help

# ---------------------------------------------------------------------------

.PHONY: help
help: ## Show this help
	@echo "$(YELLOW)django-db-mailer — make targets$(NC)"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  $(CYAN)%-20s$(NC) %s\n", $$1, $$2}'

# ---------------------------------------------------------------------------
# Install / clean
# ---------------------------------------------------------------------------

.PHONY: install
install: ## Install package only (Django + dbmail)
	$(PIP) install -e .

.PHONY: install-dev
install-dev: ## Install dev + test + demo extras
	$(PIP) install -e ".[dev,test,demo]"
	pre-commit install || true

.PHONY: clean
clean: ## Remove build artefacts and caches
	@find . -type d -name __pycache__ -prune -exec rm -rf {} +
	@find . -type f \( -name '*.pyc' -o -name '*.pyo' \) -delete
	@rm -rf build/ dist/ *.egg-info .eggs/
	@rm -rf .pytest_cache/ .mypy_cache/ .ruff_cache/ .hypothesis/
	@rm -rf .coverage coverage.xml htmlcov/

# ---------------------------------------------------------------------------
# Linters / formatters / type-check / security
# ---------------------------------------------------------------------------

.PHONY: lint
lint: ## ruff check + flake8
	ruff check .
	ruff format --check .
	flake8 dbmail

.PHONY: lint-fix
lint-fix: ## ruff format + ruff check --fix
	ruff format .
	ruff check --fix .

.PHONY: typecheck
typecheck: ## mypy on dbmail/
	mypy dbmail

.PHONY: security
security: ## bandit + pip-audit
	bandit -r dbmail -c pyproject.toml
	pip-audit

# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

.PHONY: test
test: ## Run tests (pytest)
	$(PYTEST)

.PHONY: coverage
coverage: ## Run tests with coverage and diff-cover gate
	$(PYTEST) --cov=dbmail --cov-report=term-missing --cov-report=xml --cov-report=html
	@diff-cover coverage.xml --compare-branch=origin/master --fail-under=100 || \
		echo "$(YELLOW)diff-cover threshold not met (or first run)$(NC)"

.PHONY: tox
tox: ## Run the full local matrix via tox
	tox -p auto

# ---------------------------------------------------------------------------
# Aggregate
# ---------------------------------------------------------------------------

.PHONY: check
check: lint typecheck security test ## Lint + typecheck + security + tests

# ---------------------------------------------------------------------------
# Build / release
# ---------------------------------------------------------------------------

.PHONY: build
build: clean ## Build sdist + wheel
	$(PYTHON) -m build

.PHONY: smoke-install
smoke-install: build ## Install built wheel into a fresh venv as a sanity check
	@rm -rf .smoke && $(PYTHON) -m venv .smoke
	.smoke/bin/pip install --upgrade pip
	.smoke/bin/pip install dist/*.whl Django
	.smoke/bin/python -c "import dbmail; print('OK', dbmail.__version__)"

.PHONY: release-test
release-test: build ## Upload to TestPyPI (manual smoke before real release)
	twine upload --repository testpypi dist/*

# Note: real release goes through GitHub Actions trusted publishing,
# triggered by pushing a tag. See .github/workflows/release.yml.

# ---------------------------------------------------------------------------
# Demo (Django dev server / celery worker)
# ---------------------------------------------------------------------------

.PHONY: demo-migrate
demo-migrate: ## Apply demo migrations
	cd demo && $(PYTHON) manage.py migrate

.PHONY: demo-run
demo-run: ## Run demo dev server
	cd demo && $(PYTHON) manage.py runserver

.PHONY: demo-worker
demo-worker: ## Run celery worker for demo
	cd demo && celery -A demo worker -l info -Q default

.PHONY: demo-shell
demo-shell: ## Run demo shell_plus (or shell)
	cd demo && $(PYTHON) manage.py shell_plus --print-sql || cd demo && $(PYTHON) manage.py shell

# ---------------------------------------------------------------------------
# Translations
# ---------------------------------------------------------------------------

.PHONY: messages
messages: ## Update .po files for all locales
	cd dbmail && django-admin makemessages -a --no-location

.PHONY: compilemessages
compilemessages: ## Compile .po -> .mo
	cd dbmail && django-admin compilemessages

# ---------------------------------------------------------------------------
# Docs (Sphinx)
# ---------------------------------------------------------------------------

.PHONY: docs
docs: ## Build Sphinx docs
	@rm -rf docs/_build/html
	cd docs && sphinx-build -W -b html . _build/html

.PHONY: docs-serve
docs-serve: docs ## Open built docs in a browser
	@xdg-open docs/_build/html/index.html >/dev/null 2>&1 || \
		open docs/_build/html/index.html >/dev/null 2>&1 || true
