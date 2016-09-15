# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dbmail', '0011_auto_20160803_1024'),
    ]

    operations = [
        migrations.AlterField(
            model_name='maillogemail',
            name='email',
            field=models.CharField(max_length=350, verbose_name='Recipient'),
        ),
    ]
