# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('dbmail', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='mailfromemail',
            name='email',
            field=models.CharField(help_text='For sms/tts you must specify name or number', unique=True, max_length=75, verbose_name='Email'),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='mailgroupemail',
            name='email',
            field=models.CharField(help_text=b'For sms/tts you must specify number', max_length=75, verbose_name='Email'),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='maillogemail',
            name='email',
            field=models.CharField(max_length=75),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='mailtemplate',
            name='context_note',
            field=models.TextField(help_text='This is simple note field for context variables with description.', null=True, verbose_name='Context note', blank=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='mailtemplate',
            name='from_email',
            field=models.ForeignKey(on_delete=django.db.models.deletion.SET_NULL, default=None, to='dbmail.MailFromEmail', blank=True, help_text='If not specified, then used default.', null=True, verbose_name='Message from'),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='mailtemplate',
            name='is_html',
            field=models.BooleanField(default=True, help_text='For sms/tts must be text not html', verbose_name='Is html'),
            preserve_default=True,
        ),
    ]
