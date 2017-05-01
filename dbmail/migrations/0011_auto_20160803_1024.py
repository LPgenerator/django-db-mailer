# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dbmail', '0010_auto_20160728_1645'),
    ]

    operations = [
        migrations.AlterField(
            model_name='mailsubscription',
            name='address',
            field=models.CharField(help_text='Must be phone number/email/token', max_length=255, verbose_name='Address', db_index=True),
        ),
        migrations.AlterField(
            model_name='mailsubscription',
            name='title',
            field=models.CharField(max_length=255, null=True, blank=True),
        ),
    ]
