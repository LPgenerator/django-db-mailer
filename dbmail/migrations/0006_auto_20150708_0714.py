# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('dbmail', '0005_auto_20150506_2201'),
    ]

    operations = [
        migrations.CreateModel(
            name='MailSubscription',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('backend', models.CharField(max_length=50, choices=[(b'dbmail.backends.mail', 'MailBox'), (b'dbmail.backends.push', 'Push'), (b'dbmail.backends.sms', 'SMS'), (b'dbmail.backends.tts', 'TTS')])),
                ('start_hour', models.CharField(default=b'00:00', max_length=5)),
                ('end_hour', models.CharField(default=b'23:59', max_length=5)),
                ('is_enabled', models.BooleanField(default=True, db_index=True)),
                ('is_checked', models.BooleanField(default=False, db_index=True)),
                ('defer_at_allowed_hours', models.BooleanField(default=False)),
                ('address', models.CharField(max_length=60)),
                ('user', models.ForeignKey(verbose_name='User', blank=True, to=settings.AUTH_USER_MODEL, null=True)),
            ],
            options={
                'verbose_name': 'Mail Subscription',
            },
        ),
    ]
