# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings
import dbmail.models


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('contenttypes', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='ApiKey',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=25, verbose_name='Name')),
                ('api_key', models.CharField(unique=True, max_length=32, verbose_name='Api key')),
                ('is_active', models.BooleanField(default=True, verbose_name='Is active')),
                ('created', models.DateTimeField(auto_now_add=True, verbose_name='Created')),
                ('updated', models.DateTimeField(auto_now=True, verbose_name='Updated')),
            ],
            options={
                'verbose_name': 'Mail API',
                'verbose_name_plural': 'Mail API',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='MailBcc',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('email', models.EmailField(unique=True, max_length=75, verbose_name='Email')),
                ('is_active', models.BooleanField(default=True, verbose_name='Is active')),
                ('created', models.DateTimeField(auto_now_add=True, verbose_name='Created')),
                ('updated', models.DateTimeField(auto_now=True, verbose_name='Updated')),
            ],
            options={
                'verbose_name': 'Mail Bcc',
                'verbose_name_plural': 'Mail Bcc',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='MailCategory',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(unique=True, max_length=25, verbose_name='Category')),
                ('created', models.DateTimeField(auto_now_add=True, verbose_name='Created')),
                ('updated', models.DateTimeField(auto_now=True, verbose_name='Updated')),
            ],
            options={
                'verbose_name': 'Mail category',
                'verbose_name_plural': 'Mail categories',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='MailFile',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=100, verbose_name='Name')),
                ('filename', models.FileField(upload_to=dbmail.models._upload_mail_file, verbose_name='File')),
            ],
            options={
                'verbose_name': 'Mail file',
                'verbose_name_plural': 'Mail files',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='MailFromEmail',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=100, verbose_name='Name')),
                ('email', models.EmailField(unique=True, max_length=75, verbose_name='Email')),
                ('created', models.DateTimeField(auto_now_add=True, verbose_name='Created')),
                ('updated', models.DateTimeField(auto_now=True, verbose_name='Updated')),
            ],
            options={
                'verbose_name': 'Mail from',
                'verbose_name_plural': 'Mail from',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='MailFromEmailCredential',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('host', models.CharField(max_length=50, verbose_name='Host')),
                ('port', models.PositiveIntegerField(verbose_name='Port')),
                ('username', models.CharField(max_length=50, null=True, verbose_name='Username', blank=True)),
                ('password', models.CharField(max_length=50, null=True, verbose_name='Password', blank=True)),
                ('use_tls', models.BooleanField(default=False, verbose_name='Use TLS')),
                ('fail_silently', models.BooleanField(default=False, verbose_name='Fail silently')),
                ('created', models.DateTimeField(auto_now_add=True, verbose_name='Created')),
                ('updated', models.DateTimeField(auto_now=True, verbose_name='Updated')),
            ],
            options={
                'verbose_name': 'Mail auth settings',
                'verbose_name_plural': 'Mail auth settings',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='MailGroup',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=100, verbose_name='Group name')),
                ('slug', models.SlugField(unique=True, verbose_name='Slug')),
                ('created', models.DateTimeField(auto_now_add=True, verbose_name='Created')),
                ('updated', models.DateTimeField(auto_now=True, verbose_name='Updated')),
            ],
            options={
                'verbose_name': 'Mail group',
                'verbose_name_plural': 'Mail groups',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='MailGroupEmail',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=100, verbose_name='Username')),
                ('email', models.EmailField(max_length=75, verbose_name='Email')),
                ('group', models.ForeignKey(related_name='emails', verbose_name='Group', to='dbmail.MailGroup')),
            ],
            options={
                'verbose_name': 'Mail group email',
                'verbose_name_plural': 'Mail group emails',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='MailLog',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('is_sent', models.BooleanField(default=True, db_index=True, verbose_name='Is sent')),
                ('created', models.DateTimeField(auto_now_add=True, verbose_name='Created')),
                ('error_message', models.TextField(null=True, verbose_name='Error message', blank=True)),
                ('num_of_retries', models.PositiveIntegerField(default=1, verbose_name='Number of retries')),
                ('log_id', models.CharField(max_length=60, editable=False, db_index=True)),
            ],
            options={
                'verbose_name': 'Mail log',
                'verbose_name_plural': 'Mail logs',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='MailLogEmail',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('email', models.EmailField(max_length=75)),
                ('mail_type', models.CharField(max_length=3, verbose_name='Mail type', choices=[(b'cc', b'CC'), (b'bcc', b'BCC'), (b'to', b'TO')])),
                ('log', models.ForeignKey(to='dbmail.MailLog')),
            ],
            options={
                'verbose_name': 'Mail log email',
                'verbose_name_plural': 'Mail log emails',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='MailLogException',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(unique=True, max_length=150, verbose_name='Exception')),
            ],
            options={
                'verbose_name': 'Mail Exception',
                'verbose_name_plural': 'Mail Exception',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='MailLogTrack',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('counter', models.PositiveIntegerField(default=0, verbose_name='Counter')),
                ('ip', models.GenericIPAddressField(verbose_name='IP')),
                ('ua', models.CharField(max_length=350, null=True, verbose_name='User Agent', blank=True)),
                ('ua_os', models.CharField(max_length=100, null=True, verbose_name='OS', blank=True)),
                ('ua_os_version', models.CharField(max_length=100, null=True, verbose_name='OS version', blank=True)),
                ('ua_dist', models.CharField(max_length=20, null=True, verbose_name='Dist name', blank=True)),
                ('ua_dist_version', models.CharField(max_length=100, null=True, verbose_name='Dist version', blank=True)),
                ('ua_browser', models.CharField(max_length=100, null=True, verbose_name='Browser', blank=True)),
                ('ua_browser_version', models.CharField(max_length=20, null=True, verbose_name='Browser version', blank=True)),
                ('ip_area_code', models.CharField(max_length=255, null=True, verbose_name='Area code', blank=True)),
                ('ip_city', models.CharField(max_length=255, null=True, verbose_name='City', blank=True)),
                ('ip_country_code', models.CharField(max_length=255, null=True, verbose_name='Country code', blank=True)),
                ('ip_country_code3', models.CharField(max_length=255, null=True, verbose_name='Country code3', blank=True)),
                ('ip_country_name', models.CharField(max_length=255, null=True, verbose_name='Country name', blank=True)),
                ('ip_dma_code', models.CharField(max_length=255, null=True, verbose_name='Dma code', blank=True)),
                ('ip_latitude', models.CharField(max_length=255, null=True, verbose_name='Latitude', blank=True)),
                ('ip_longitude', models.CharField(max_length=255, null=True, verbose_name='Longitude', blank=True)),
                ('ip_postal_code', models.CharField(max_length=255, null=True, verbose_name='Postal code', blank=True)),
                ('ip_region', models.CharField(max_length=255, null=True, verbose_name='Region', blank=True)),
                ('is_read', models.BooleanField(default=False, verbose_name='Is read')),
                ('created', models.DateTimeField(auto_now_add=True, verbose_name='Created')),
                ('updated', models.DateTimeField(auto_now=True, verbose_name='Updated')),
                ('mail_log', models.ForeignKey(verbose_name='Log', to='dbmail.MailLog')),
            ],
            options={
                'verbose_name': 'Mail Tracking',
                'verbose_name_plural': 'Mail Tracking',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='MailTemplate',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=100, verbose_name='Template name', db_index=True)),
                ('subject', models.CharField(max_length=100, verbose_name='Subject')),
                ('message', models.TextField(verbose_name='Body')),
                ('slug', models.SlugField(help_text='Unique slug to use in code.', unique=True, verbose_name='Slug')),
                ('num_of_retries', models.PositiveIntegerField(default=1, verbose_name='Number of retries')),
                ('priority', models.SmallIntegerField(default=6, verbose_name='Priority', choices=[(0, 'High'), (3, 'Medium'), (6, 'Low'), (9, 'Deferred')])),
                ('is_html', models.BooleanField(default=True, verbose_name='Is html')),
                ('is_admin', models.BooleanField(default=False, verbose_name='For admin')),
                ('is_active', models.BooleanField(default=True, verbose_name='Is active')),
                ('enable_log', models.BooleanField(default=True, verbose_name='Logging enabled')),
                ('created', models.DateTimeField(auto_now_add=True, verbose_name='Created')),
                ('updated', models.DateTimeField(auto_now=True, verbose_name='Updated')),
                ('context_note', models.TextField(help_text='This is simple note field for context variables with description', null=True, verbose_name='Context note', blank=True)),
                ('interval', models.PositiveIntegerField(help_text='\n            Specify interval to send messages after sometime.\n            Interval must be set in the seconds.\n            ', null=True, verbose_name='Send interval', blank=True)),
                ('bcc_email', models.ManyToManyField(help_text=b'Blind carbon copy', to='dbmail.MailBcc', null=True, verbose_name='Bcc', blank=True)),
                ('category', models.ForeignKey(default=None, blank=True, to='dbmail.MailCategory', null=True, verbose_name='Category')),
                ('from_email', models.ForeignKey(default=None, to='dbmail.MailFromEmail', blank=True, help_text='If not specified, then used default.', null=True, verbose_name='From email')),
            ],
            options={
                'verbose_name': 'Mail template',
                'verbose_name_plural': 'Mail templates',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Signal',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=100, verbose_name='Name')),
                ('signal', models.CharField(default=b'post_save', max_length=15, verbose_name='Signal', choices=[(b'pre_save', b'pre_save'), (b'post_save', b'post_save'), (b'pre_delete', b'pre_delete'), (b'post_delete', b'post_delete'), (b'm2m_changed', b'm2m_changed')])),
                ('rules', models.TextField(default=b'{{ instance.email }}', help_text='Template should return email to send message. Example:{% if instance.is_active %}{{ instance.email }}{% endif %}.You can return a multiple emails separated by commas.', null=True, verbose_name='Rules', blank=True)),
                ('created', models.DateTimeField(auto_now_add=True, verbose_name='Created')),
                ('updated', models.DateTimeField(auto_now=True, verbose_name='Updated')),
                ('is_active', models.BooleanField(default=True, verbose_name='Is active')),
                ('receive_once', models.BooleanField(default=True, help_text='Signal will be receive and send once for new db row.', verbose_name='Receive once')),
                ('interval', models.PositiveIntegerField(help_text='Specify interval to send messages after sometime. That very helpful for mailing on enterprise products.Interval must be set in the seconds.', null=True, verbose_name='Send interval', blank=True)),
                ('update_model', models.BooleanField(default=False, help_text='\n            If you are using interval and want to update object state,\n            you can use this flag and refer to the variable\n            {{current_instance}}\n            ', verbose_name='Update model state')),
                ('group', models.ForeignKey(blank=True, to='dbmail.MailGroup', help_text='You can use group email or rules for recipients.', null=True, verbose_name='Email group')),
                ('model', models.ForeignKey(verbose_name='Model', to='contenttypes.ContentType')),
                ('template', models.ForeignKey(verbose_name='Template', to='dbmail.MailTemplate')),
            ],
            options={
                'verbose_name': 'Mail signal',
                'verbose_name_plural': 'Mail signals',
            },
            bases=(models.Model,),
        ),
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
        migrations.CreateModel(
            name='SignalLog',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('model_pk', models.BigIntegerField()),
                ('created', models.DateTimeField(auto_now_add=True, verbose_name='Created')),
                ('model', models.ForeignKey(to='contenttypes.ContentType')),
                ('signal', models.ForeignKey(to='dbmail.Signal')),
            ],
            options={
                'verbose_name': 'Signal log',
                'verbose_name_plural': 'Signal logs',
            },
            bases=(models.Model,),
        ),
        migrations.AlterIndexTogether(
            name='signaldeferreddispatch',
            index_together=set([('eta', 'done')]),
        ),
        migrations.AddField(
            model_name='maillog',
            name='error_exception',
            field=models.ForeignKey(verbose_name='Exception', blank=True, to='dbmail.MailLogException', null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='maillog',
            name='template',
            field=models.ForeignKey(verbose_name='Template', to='dbmail.MailTemplate'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='maillog',
            name='user',
            field=models.ForeignKey(verbose_name='User', blank=True, to=settings.AUTH_USER_MODEL, null=True),
            preserve_default=True,
        ),
        migrations.AlterUniqueTogether(
            name='mailgroupemail',
            unique_together=set([('email', 'group')]),
        ),
        migrations.AddField(
            model_name='mailfromemail',
            name='credential',
            field=models.ForeignKey(default=None, blank=True, to='dbmail.MailFromEmailCredential', null=True, verbose_name='Auth credentials'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='mailfile',
            name='template',
            field=models.ForeignKey(related_name='files', verbose_name='Template', to='dbmail.MailTemplate'),
            preserve_default=True,
        ),
    ]
