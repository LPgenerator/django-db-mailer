"""Sandboxed template renderer based on Jinja2.

The default Django ``Template`` engine evaluates attribute access against
the context, which means a staff user with ``dbmail.change_mailtemplate``
permission can craft a template body such as ``{{ instance.__class__.
__init__.__globals__... }}`` and traverse to ``django.conf.settings`` —
a classic Server-Side Template Injection (SSTI) vector (audit item M-1).

Switching the entire codebase to Jinja2 is not viable: existing operators
ship templates that use ``{% load %}``, ``{% url %}`` and other Django
template tags.  Instead, the sandbox is **opt-in** via
``DB_MAILER_USE_JINJA2_SANDBOX = True``.  When enabled, every
``MailTemplate`` body and subject is rendered through
``jinja2.sandbox.SandboxedEnvironment``, which restricts access to dunder
attributes, module internals and other unsafe operations.

Trade-off: Django-only constructs (``{% load %}``, ``{% url %}``,
``{{ form|as_crispy_field }}`` and so on) become unavailable for
operators who flip the switch.  This is documented behaviour — the flag
defaults to ``False`` so existing deployments are unaffected.

The Jinja2 dependency is declared as an optional extra
(``pip install django-db-mailer[sandbox]``) so the package stays slim
for users who do not need the hardened renderer.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:  # pragma: no cover - typing only
    from jinja2.sandbox import SandboxedEnvironment


_JINJA2_INSTALL_HINT = (
    "Jinja2 is required for DB_MAILER_USE_JINJA2_SANDBOX=True. Install it with: pip install 'django-db-mailer[sandbox]'"
)


def _build_environment() -> SandboxedEnvironment:
    """Import Jinja2 lazily and construct a hardened sandbox environment.

    Importing inside the function keeps Jinja2 strictly optional: users
    who never flip the sandbox flag do not pay an import cost and do not
    need the dependency installed.
    """
    try:
        from jinja2.sandbox import SandboxedEnvironment
    except ImportError as exc:  # pragma: no cover - exercised via test
        raise ImportError(_JINJA2_INSTALL_HINT) from exc

    return SandboxedEnvironment(autoescape=True)


class SandboxedRenderer:
    """Render ``MailTemplate`` strings inside a Jinja2 sandbox.

    The class is instantiated once per render call by ``Sender._render_template``
    (mail bodies are short-lived, so caching the environment buys nothing).
    Construction lazily imports Jinja2 and raises ``ImportError`` with a
    helpful message if the package is missing — the error surfaces only
    when an operator actually enables the sandbox.
    """

    def __init__(self) -> None:
        self._env = _build_environment()

    def render(self, template_str: str, context: dict[str, Any]) -> str:
        """Render ``template_str`` against ``context`` in the sandbox.

        Jinja2's ``SandboxedEnvironment`` raises
        ``jinja2.exceptions.SecurityError`` when a template touches a
        forbidden attribute (``__class__``, ``__init__``, ``__globals__``,
        ``__bases__``, ``mro`` and friends).  We let that exception
        propagate so the caller can log it and surface a 500 — silently
        swallowing security errors would defeat the point of the sandbox.
        """
        template = self._env.from_string(template_str)
        return template.render(**context)
