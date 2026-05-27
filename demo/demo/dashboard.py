"""Grappelli dashboard for the django-db-mailer demo.

Adapted (not removed) for Grappelli 4.x. Referenced by
``GRAPPELLI_INDEX_DASHBOARD`` in settings; if Grappelli is not
installed the import fails silently and the default Django admin
index is used.
"""

from __future__ import annotations

try:
    from grappelli.dashboard import Dashboard, modules
except ImportError:  # pragma: no cover — exercised only without grappelli
    Dashboard = object  # type: ignore[assignment, misc]
    modules = None  # type: ignore[assignment]


class DBMailerDashboard(Dashboard):
    """Two-column dashboard listing dbmail models and recent admin actions."""

    def init_with_context(self, context):
        if modules is None:
            return
        self.children.append(
            modules.ModelList(
                title="DBMailer",
                column=1,
                collapsible=True,
                models=("dbmail.models.*",),
            )
        )
        self.children.append(
            modules.RecentActions(
                title="Recent Actions",
                column=2,
                limit=10,
            )
        )
