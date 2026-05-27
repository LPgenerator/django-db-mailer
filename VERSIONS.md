# Versioning Strategy

`django-db-mailer` uses a modified version of [Semantic Versioning][semver] for
all changes to the project. It is strongly encouraged that you pin at least the
major version and potentially the minor version to avoid pulling in breaking
changes.

Semantic versions take the form of `MAJOR.MINOR.PATCH`.

When bugs are fixed in the project in a backwards-compatible way, the `PATCH`
level will be incremented by one. When new features are added to the project
in a backwards-compatible way, the `PATCH` level will be incremented by one.
`PATCH` changes should _not_ break your code and are generally safe for upgrade.

When a new large feature set comes online or a small breaking change is
introduced, the `MINOR` version will be incremented by one and the `PATCH`
version reset to zero. `MINOR` changes _may_ require some amount of manual
code change for upgrade. These backwards-incompatible changes will generally
be limited to a small number of function signatures, settings names, or
provider interfaces.

The `MAJOR` version is used to indicate the family of technology represented
by the project. Breaking changes that require extensive reworking of code
will cause the `MAJOR` version to be incremented by one, and the `MINOR`
and `PATCH` versions will be reset to zero. We understand that this can be
disruptive, so this type of breaking change will only be introduced when
absolutely necessary. New `MAJOR` versions will be communicated in advance
with **Release Candidates** and a schedule.

## Supported Versions

Only the current `MAJOR` version of `django-db-mailer` receives new features
and functionality. Bug fixes and security updates may be backported to the
previous `MAJOR` version for a limited time after a new major release.

| Version | Status              | Python      | Django                  |
|---------|---------------------|-------------|-------------------------|
| `3.x`   | ✅ Active            | 3.10 – 3.14 | 4.2 LTS, 5.2 LTS, 6.0   |
| `2.5.x` | ⚠️ Critical fixes    | 3.6 – 3.9   | 2.2 – 3.2               |
| `< 2.5` | ❌ End of life       | —           | —                       |

Backport policy for `2.5.x` ends when the Django 3.2 support window ends
upstream (April 2024 already passed; we keep `2.5.x` for emergency security
patches only, no feature backports).

## Supported Python and Django matrix

Each minor release of `django-db-mailer 3.x` is tested against:

- Python: minimum + maximum of currently supported CPython versions.
- Django: each currently supported LTS that is compatible with the supported
  Python range.

When a new Python or Django LTS is released, support is added in the next
**MINOR** version. When an old Python or Django version reaches its upstream
end of life, it is dropped in the next **MAJOR** version after a deprecation
notice in `CHANGELOG.md` at least one MINOR ahead.

## Deprecation policy

- A feature, setting, or provider may be deprecated in any `MINOR` release.
- A `DeprecationWarning` is emitted at runtime, and the deprecation is
  documented in `CHANGELOG.md` and in the relevant section of the docs.
- A deprecated feature is kept for **at least one full MINOR cycle** after
  the warning is introduced, and is removed only in the next `MAJOR` release.
- End-of-life third-party services (for example, Parse.com, Boxcar) keep
  working code paths until the next `MAJOR` release; they only emit
  `DeprecationWarning` on first use.

## Pre-release versions

- `X.Y.Z.devN` — internal development snapshot, not published to PyPI.
- `X.Y.ZrcN` — release candidate, may be published to TestPyPI.
- `X.Y.Z` — stable release, published to PyPI through trusted publishing.

## Release cadence

- `PATCH` — as needed (security/bug fixes).
- `MINOR` — roughly every 3–6 months, aligned with Django LTS releases.
- `MAJOR` — only when forced by upstream EOL (Python, Django) or when
  accumulated breaking changes justify a coordinated migration.

[semver]: https://semver.org
