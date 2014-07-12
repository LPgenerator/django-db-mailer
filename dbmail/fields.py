# -*- encoding: utf-8 -*-

try:
    from tinymce.models import HTMLField

except ImportError:
    from django.db import models

    HTMLField = models.TextField
