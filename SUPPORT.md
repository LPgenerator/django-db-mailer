# Where to ask questions

Different kinds of input go to different places — please pick the right one.

| You want to... | Use |
|----------------|-----|
| Report a bug                                          | Open an Issue with the **Bug report** template. |
| Ask for a new feature                                  | Open an Issue with the **Feature request** template. |
| Add a new provider (SMS, push, voice, bot)             | Open an Issue with the **Provider request** template. |
| Ask a how-to question                                  | Use **GitHub Discussions → Q&A**. |
| Share a project that uses django-db-mailer             | Use **GitHub Discussions → Show and tell**. |
| Track release announcements                            | Watch the repo or read **GitHub Discussions → Announcements**. |

For private security reports, open a private GitHub Security Advisory
from the **Security** tab of the repository.

## Before opening an Issue

- Search the existing issues — your question may already be answered.
- Read the [README.md](README.md), [CHANGELOG.md](CHANGELOG.md) and
  [MIGRATION.md](MIGRATION.md) — most upgrade questions are covered there.
- Reproduce on the latest released version of `django-db-mailer`. We
  rarely backport fixes to older minor lines.

## What makes a good Issue

- Python and Django versions (`python --version`, `django.get_version()`).
- Database engine and version (PostgreSQL / MySQL / SQLite, `X.Y`).
- Minimal reproducible example — preferably a 10-line snippet, not a
  pointer to your private project.
- Full traceback if there is an error.
- What you expected to happen vs. what actually happens.

## Response time

This is a single-maintainer open-source project. We try to acknowledge
issues within a week. Pull requests are easier to merge than issues are
to fix — if you can send a PR, please do.
