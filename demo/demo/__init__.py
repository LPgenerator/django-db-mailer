from __future__ import annotations

# Make sure the Celery app is loaded when Django starts so that shared_task
# can use it. The app object is also re-exported as ``demo.celery_app`` for
# call sites that prefer that name.
from .celery import app as celery_app

__all__ = ("celery_app",)
