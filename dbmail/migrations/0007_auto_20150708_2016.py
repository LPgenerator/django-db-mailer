# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('dbmail', '0006_auto_20150708_0714'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='mailsubscription',
            options={'verbose_name': 'Mail Subscription', 'verbose_name_plural': 'Mail Subscriptions'},
        ),
        migrations.AlterField(
            model_name='mailsubscription',
            name='address',
            field=models.CharField(help_text='Must be phone number/email/token', unique=True, max_length=60, verbose_name='Address'),
        ),
        migrations.AlterField(
            model_name='mailsubscription',
            name='backend',
            field=models.CharField(default=b'dbmail.backends.mail', max_length=50, verbose_name='Backend', choices=[(b'dbmail.backends.mail', 'MailBox'), (b'dbmail.backends.push', 'Push'), (b'dbmail.backends.sms', 'SMS'), (b'dbmail.backends.tts', 'TTS')]),
        ),
        migrations.AlterField(
            model_name='mailsubscription',
            name='defer_at_allowed_hours',
            field=models.BooleanField(default=False, verbose_name='Defer at allowed hours'),
        ),
        migrations.AlterField(
            model_name='mailsubscription',
            name='end_hour',
            field=models.CharField(default=b'23:59', max_length=5, verbose_name='End hour'),
        ),
        migrations.AlterField(
            model_name='mailsubscription',
            name='is_checked',
            field=models.BooleanField(default=False, db_index=True, verbose_name='Is checked'),
        ),
        migrations.AlterField(
            model_name='mailsubscription',
            name='is_enabled',
            field=models.BooleanField(default=True, db_index=True, verbose_name='Is enabled'),
        ),
        migrations.AlterField(
            model_name='mailsubscription',
            name='start_hour',
            field=models.CharField(default=b'00:00', max_length=5, verbose_name='Start hour'),
        ),
    ]
