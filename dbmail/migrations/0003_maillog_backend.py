# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('dbmail', '0002_auto_20150321_1539'),
    ]

    operations = [
        migrations.AddField(
            model_name='maillog',
            name='backend',
            field=models.CharField(default=b'mail', editable=False, choices=[(b'tts', b'dbmail.backends.tts'), (b'mail', b'dbmail.backends.mail'), (b'sms', b'dbmail.backends.sms')], max_length=25, verbose_name='Backend', db_index=True),
            preserve_default=True,
        ),
    ]
