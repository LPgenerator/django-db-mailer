# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import ckeditor.fields


class Migration(migrations.Migration):

    dependencies = [
        ('dbmail', '0012_auto_20160915_1340'),
    ]

    operations = [
        migrations.AddField(
            model_name='maillogexception',
            name='ignore',
            field=models.BooleanField(default=False, verbose_name='Ignore'),
        ),
    ]
