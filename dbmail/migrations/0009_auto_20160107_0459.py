# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dbmail', '0008_auto_20151007_1918'),
    ]

    operations = [
        migrations.AlterField(
            model_name='mailtemplate',
            name='subject',
            field=models.TextField(verbose_name='Subject'),
        ),
    ]
