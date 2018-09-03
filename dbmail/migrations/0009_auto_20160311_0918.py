# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dbmail', '0008_auto_20151007_1918'),
    ]

    operations = [
        migrations.AlterField(
            model_name='mailsubscription',
            name='address',
            field=models.CharField(help_text='Must be phone number/email/token', max_length=60, verbose_name='Address', db_index=True),
        ),
    ]
