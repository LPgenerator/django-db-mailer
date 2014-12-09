# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('dbmail', '0001_initial'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='signallog',
            options={'verbose_name': 'Signal log', 'verbose_name_plural': 'Signal logs'},
        ),
        migrations.AddField(
            model_name='mailtemplate',
            name='interval',
            field=models.PositiveIntegerField(help_text='\n            Specify interval to send messages after sometime.\n            Interval must be set in the seconds.\n            ', null=True, verbose_name='Send interval', blank=True),
            preserve_default=True,
        ),
    ]
