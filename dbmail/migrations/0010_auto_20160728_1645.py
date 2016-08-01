# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dbmail', '0009_auto_20160311_0918'),
    ]

    operations = [
        migrations.AddField(
            model_name='mailsubscription',
            name='data',
            field=models.TextField(null=True, blank=True),
        ),
        migrations.AddField(
            model_name='mailsubscription',
            name='title',
            field=models.CharField(max_length=100, null=True, blank=True),
        ),
    ]
