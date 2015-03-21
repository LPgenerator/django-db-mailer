# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('dbmail', '0003_maillog_backend'),
    ]

    operations = [
        migrations.AddField(
            model_name='maillog',
            name='provider',
            field=models.CharField(default=None, editable=False, max_length=250, blank=True, null=True, verbose_name='Backend', db_index=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='maillog',
            name='backend',
            field=models.CharField(default=b'mail', editable=False, choices=[(b'tts', b'dbmail.backends.tts'), (b'mail', b'dbmail.backends.mail'), (b'sms', b'dbmail.backends.sms'), (b'push', b'dbmail.backends.push')], max_length=25, verbose_name='Backend', db_index=True),
            preserve_default=True,
        ),
    ]
