"""HTML field selector for ``MailTemplate`` / ``MailBaseTemplate``.

The schema column is always a ``TextField`` regardless of which
rich-text widget is installed — this keeps migrations stable across
installs that have or do not have ``django-tinymce`` /
``django-ckeditor``. The chosen widget is plugged in only at the
form/admin level via ``HTMLField`` below.

The decision is gated by ``INSTALLED_APPS`` (``app_installed``) at
import time, so the migration recorded by Django never depends on
``ckeditor.fields`` / ``tinymce.models`` being importable.
"""

from __future__ import annotations

from django.db import models

from dbmail import app_installed

HTMLField = models.TextField
DataTextField = models.TextField

if app_installed("tinymce"):
    from tinymce.models import HTMLField

if app_installed("ckeditor"):
    from ckeditor.fields import RichTextField as HTMLField
