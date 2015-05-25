# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):
    dependencies = [
        ('dbmail', '0004_auto_20150321_2214'),
    ]

    operations = [
        migrations.CreateModel(
            name='MailBaseTemplate',
            fields=[
                ('id', models.AutoField(
                    verbose_name='ID', serialize=False,
                    auto_created=True, primary_key=True)),
                ('name', models.CharField(
                    unique=True, max_length=100, verbose_name='Name')),
                ('message', models.TextField(
                    help_text='Basic template for mail messages. '
                              '{{content}} tag for msg.',
                    verbose_name='Body')),
                ('created', models.DateTimeField(
                    auto_now_add=True, verbose_name='Created')),
                ('updated', models.DateTimeField(
                    auto_now=True, verbose_name='Updated')),
            ],
            options={
                'verbose_name': 'Mail base template',
                'verbose_name_plural': 'Mail base templates',
            },
        ),
        migrations.AddField(
            model_name='mailtemplate',
            name='base',
            field=models.ForeignKey(
                verbose_name='Basic template', blank=True,
                to='dbmail.MailBaseTemplate', null=True),
        ),
    ]
