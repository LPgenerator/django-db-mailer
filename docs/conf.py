"""Sphinx configuration for django-db-mailer documentation.

Modernized in 3.0:
- Python-based config (no execfile gymnastics).
- MyST-Parser enabled - Markdown only (RST removed in 3.0).
- Furo theme.
- Read the Docs friendly via .readthedocs.yaml.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

# Repo layout: docs/conf.py is one level below the package root.
REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

import dbmail  # noqa: E402

# ---------------------------------------------------------------------------
# Project metadata
# ---------------------------------------------------------------------------
project = "django-db-mailer"
copyright = "2014-2026, GoTLiuM InSPiRiT"
author = "GoTLiuM InSPiRiT"
version = dbmail.__version__
release = dbmail.__version__

# ---------------------------------------------------------------------------
# General configuration
# ---------------------------------------------------------------------------
extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.intersphinx",
    "sphinx.ext.viewcode",
    "sphinx.ext.todo",
    "myst_parser",
    "sphinx_copybutton",
    "sphinxext.opengraph",
]

# Open Graph / Twitter card metadata for SEO + previews on
# GitHub / Telegram / Slack share unfurls.
ogp_site_url = "https://django-db-mailer.readthedocs.io/"
ogp_site_name = "django-db-mailer"
ogp_description_length = 200
ogp_type = "website"

source_suffix = {
    ".md": "markdown",
}

master_doc = "index"
language = "en"

exclude_patterns = ["_build", "Thumbs.db", ".DS_Store", "legacy/**"]

intersphinx_mapping = {
    "python": ("https://docs.python.org/3", None),
    "django": (
        "https://docs.djangoproject.com/en/stable/",
        "https://docs.djangoproject.com/en/stable/_objects/",
    ),
    "celery": ("https://docs.celeryq.dev/en/stable/", None),
}

todo_include_todos = False

# ---------------------------------------------------------------------------
# MyST options
# ---------------------------------------------------------------------------
myst_enable_extensions = [
    "colon_fence",
    "deflist",
    "fieldlist",
    "substitution",
    "tasklist",
]
myst_heading_anchors = 3

# ---------------------------------------------------------------------------
# HTML output
# ---------------------------------------------------------------------------
try:
    import furo  # noqa: F401

    html_theme = "furo"
except ImportError:
    html_theme = "alabaster"

html_static_path = []
html_show_sourcelink = False
html_title = f"django-db-mailer {release}"

# ---------------------------------------------------------------------------
# Autodoc - configure Django settings before autoimport.
# ---------------------------------------------------------------------------
autodoc_default_options = {
    "members": True,
    "undoc-members": False,
    "show-inheritance": True,
}
autoclass_content = "class"

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "tests.settings")
try:
    import django

    django.setup()
except Exception:
    # Don't block the build when Django is missing in restrictive envs.
    pass
