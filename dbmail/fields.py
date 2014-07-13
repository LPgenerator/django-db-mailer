# -*- encoding: utf-8 -*-

from django.conf import settings
from django.db import models

HTMLField = models.TextField

if 'tinymce' in settings.INSTALLED_APPS:
    try:
        from tinymce.models import HTMLField

    except ImportError:
        pass
