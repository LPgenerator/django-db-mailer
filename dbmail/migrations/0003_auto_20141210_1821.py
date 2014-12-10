# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('dbmail', '0002_auto_20141209_0544'),
    ]

    operations = [
        migrations.CreateModel(
            name='SignalDeferredDispatch',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('args', models.TextField()),
                ('kwargs', models.TextField()),
                ('params', models.TextField()),
                ('eta', models.DateTimeField(db_index=True)),
                ('done', models.NullBooleanField(default=None)),
                ('created', models.DateTimeField(auto_now_add=True)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.AlterIndexTogether(
            name='signaldeferreddispatch',
            index_together=set([('eta', 'done')]),
        ),
        migrations.AddField(
            model_name='signal',
            name='update_model',
            field=models.BooleanField(default=False, help_text='\n            If you are using interval and want to update object state,\n            you can use this flag and refer to the variable\n            {{current_instance}}\n            ', verbose_name='Update model state'),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='signal',
            name='interval',
            field=models.PositiveIntegerField(help_text='Specify interval to send messages after sometime. That very helpful for mailing on enterprise products.Interval must be set in the seconds.', null=True, verbose_name='Send interval', blank=True),
            preserve_default=True,
        ),
    ]
