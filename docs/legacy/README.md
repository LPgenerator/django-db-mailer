# Legacy artefacts

This folder preserves files that used to ship with `django-db-mailer 2.x`
but no longer reflect the supported developer workflow:

- `Vagrantfile` — replaced by Docker Compose. See `docker-compose.yml`
  and `docs/demo.md` for the modern setup.

These files are kept for git-history traceability only; they are not
included in built Docker images, the Sphinx HTML site, or the wheel.
