# -*- encoding: utf-8 -*-

from django.db import models

from dbmail import app_installed

HTMLField = models.TextField

if app_installed('tinymce'):
    try:
        from tinymce.models import HTMLField

    except ImportError:
        pass
