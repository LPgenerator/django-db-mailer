# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dbmail', '0007_auto_20150708_2016'),
    ]

    operations = [

        migrations.AlterField(
            model_name='mailbcc',
            name='email',
            field=models.EmailField(unique=True, max_length=254, verbose_name='Email'),
        ),
        migrations.AlterField(
            model_name='mailfromemail',
            name='email',
            field=models.CharField(help_text='For sms/tts/push you must specify name or number', unique=True, max_length=75, verbose_name='Email'),
        ),
        migrations.AlterField(
            model_name='maillog',
            name='log_id',
            field=models.CharField(verbose_name='Log ID', max_length=60, editable=False, db_index=True),
        ),
        migrations.AlterField(
            model_name='maillog',
            name='provider',
            field=models.CharField(default=None, editable=False, max_length=250, blank=True, null=True, verbose_name='Provider', db_index=True),
        ),
        migrations.AlterField(
            model_name='maillogemail',
            name='email',
            field=models.CharField(max_length=75, verbose_name='Recipient'),
        ),
        migrations.AlterField(
            model_name='mailtemplate',
            name='bcc_email',
            field=models.ManyToManyField(help_text=b'Blind carbon copy', to='dbmail.MailBcc', verbose_name='Bcc', blank=True),
        ),
        migrations.AlterField(
            model_name='mailtemplate',
            name='is_html',
            field=models.BooleanField(default=True, help_text='For sms/tts/push must be text not html', verbose_name='Is html'),
        ),
    ]
