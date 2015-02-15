# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'MailLogTrack'
        db.create_table('dbmail_maillogtrack', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('mail_log', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['dbmail.MailLog'])),
            ('counter', self.gf('django.db.models.fields.PositiveIntegerField')(default=0)),
            ('ip', self.gf('django.db.models.fields.GenericIPAddressField')(max_length=39)),
            ('ua', self.gf('django.db.models.fields.CharField')(max_length=350, null=True, blank=True)),
            ('ua_os', self.gf('django.db.models.fields.CharField')(max_length=100, null=True, blank=True)),
            ('ua_os_version', self.gf('django.db.models.fields.CharField')(max_length=100, null=True, blank=True)),
            ('ua_dist', self.gf('django.db.models.fields.CharField')(max_length=20, null=True, blank=True)),
            ('ua_dist_version', self.gf('django.db.models.fields.CharField')(max_length=100, null=True, blank=True)),
            ('ua_browser', self.gf('django.db.models.fields.CharField')(max_length=100, null=True, blank=True)),
            ('ua_browser_version', self.gf('django.db.models.fields.CharField')(max_length=20, null=True, blank=True)),
            ('ip_area_code', self.gf('django.db.models.fields.CharField')(max_length=255, null=True, blank=True)),
            ('ip_city', self.gf('django.db.models.fields.CharField')(max_length=255, null=True, blank=True)),
            ('ip_country_code', self.gf('django.db.models.fields.CharField')(max_length=255, null=True, blank=True)),
            ('ip_country_code3', self.gf('django.db.models.fields.CharField')(max_length=255, null=True, blank=True)),
            ('ip_country_name', self.gf('django.db.models.fields.CharField')(max_length=255, null=True, blank=True)),
            ('ip_dma_code', self.gf('django.db.models.fields.CharField')(max_length=255, null=True, blank=True)),
            ('ip_latitude', self.gf('django.db.models.fields.CharField')(max_length=255, null=True, blank=True)),
            ('ip_longitude', self.gf('django.db.models.fields.CharField')(max_length=255, null=True, blank=True)),
            ('ip_postal_code', self.gf('django.db.models.fields.CharField')(max_length=255, null=True, blank=True)),
            ('ip_region', self.gf('django.db.models.fields.CharField')(max_length=255, null=True, blank=True)),
            ('is_read', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('created', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('updated', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
        ))
        db.send_create_signal('dbmail', ['MailLogTrack'])

        # Adding field 'MailLog.log_id'
        db.add_column('dbmail_maillog', 'log_id',
                      self.gf('django.db.models.fields.CharField')(default='X', max_length=60, db_index=True),
                      keep_default=False)


    def backwards(self, orm):
        # Deleting model 'MailLogTrack'
        db.delete_table('dbmail_maillogtrack')

        # Deleting field 'MailLog.log_id'
        db.delete_column('dbmail_maillog', 'log_id')


    models = {
        'auth.group': {
            'Meta': {'object_name': 'Group'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '80'}),
            'permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'})
        },
        'auth.permission': {
            'Meta': {'ordering': "('content_type__app_label', 'content_type__model', 'codename')", 'unique_together': "(('content_type', 'codename'),)", 'object_name': 'Permission'},
            'codename': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['contenttypes.ContentType']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        'auth.user': {
            'Meta': {'object_name': 'User'},
            'date_joined': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75', 'blank': 'True'}),
            'first_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'groups': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Group']", 'symmetrical': 'False', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'is_staff': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_superuser': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'last_login': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'last_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'user_permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'}),
            'username': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '30'})
        },
        'contenttypes.contenttype': {
            'Meta': {'ordering': "('name',)", 'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        'dbmail.apikey': {
            'Meta': {'object_name': 'ApiKey'},
            'api_key': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '32'}),
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '25'}),
            'updated': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'})
        },
        'dbmail.mailbcc': {
            'Meta': {'object_name': 'MailBcc'},
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'email': ('django.db.models.fields.EmailField', [], {'unique': 'True', 'max_length': '75'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'updated': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'})
        },
        'dbmail.mailcategory': {
            'Meta': {'object_name': 'MailCategory'},
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '25'}),
            'updated': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'})
        },
        'dbmail.mailfile': {
            'Meta': {'object_name': 'MailFile'},
            'filename': ('django.db.models.fields.files.FileField', [], {'max_length': '100'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'template': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'files'", 'to': "orm['dbmail.MailTemplate']"})
        },
        'dbmail.mailfromemail': {
            'Meta': {'object_name': 'MailFromEmail'},
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'credential': ('django.db.models.fields.related.ForeignKey', [], {'default': 'None', 'to': "orm['dbmail.MailFromEmailCredential']", 'null': 'True', 'blank': 'True'}),
            'email': ('django.db.models.fields.EmailField', [], {'unique': 'True', 'max_length': '75'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'updated': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'})
        },
        'dbmail.mailfromemailcredential': {
            'Meta': {'object_name': 'MailFromEmailCredential'},
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'fail_silently': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'host': ('django.db.models.fields.CharField', [], {'max_length': '50'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '50', 'null': 'True', 'blank': 'True'}),
            'port': ('django.db.models.fields.PositiveIntegerField', [], {}),
            'updated': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'use_tls': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'username': ('django.db.models.fields.CharField', [], {'max_length': '50', 'null': 'True', 'blank': 'True'})
        },
        'dbmail.mailgroup': {
            'Meta': {'object_name': 'MailGroup'},
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'slug': ('django.db.models.fields.SlugField', [], {'unique': 'True', 'max_length': '50'}),
            'updated': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'})
        },
        'dbmail.mailgroupemail': {
            'Meta': {'unique_together': "(('email', 'group'),)", 'object_name': 'MailGroupEmail'},
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75'}),
            'group': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'emails'", 'to': "orm['dbmail.MailGroup']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        'dbmail.maillog': {
            'Meta': {'object_name': 'MailLog'},
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'error_exception': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['dbmail.MailLogException']", 'null': 'True', 'blank': 'True'}),
            'error_message': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_sent': ('django.db.models.fields.BooleanField', [], {'default': 'True', 'db_index': 'True'}),
            'log_id': ('django.db.models.fields.CharField', [], {'max_length': '60', 'db_index': 'True'}),
            'num_of_retries': ('django.db.models.fields.PositiveIntegerField', [], {'default': '1'}),
            'template': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['dbmail.MailTemplate']"}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']", 'null': 'True', 'blank': 'True'})
        },
        'dbmail.maillogemail': {
            'Meta': {'object_name': 'MailLogEmail'},
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'log': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['dbmail.MailLog']"}),
            'mail_type': ('django.db.models.fields.CharField', [], {'max_length': '3'})
        },
        'dbmail.maillogexception': {
            'Meta': {'object_name': 'MailLogException'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '150'})
        },
        'dbmail.maillogtrack': {
            'Meta': {'object_name': 'MailLogTrack'},
            'counter': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'ip': ('django.db.models.fields.GenericIPAddressField', [], {'max_length': '39'}),
            'ip_area_code': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'ip_city': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'ip_country_code': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'ip_country_code3': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'ip_country_name': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'ip_dma_code': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'ip_latitude': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'ip_longitude': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'ip_postal_code': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'ip_region': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'is_read': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'mail_log': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['dbmail.MailLog']"}),
            'ua': ('django.db.models.fields.CharField', [], {'max_length': '350', 'null': 'True', 'blank': 'True'}),
            'ua_browser': ('django.db.models.fields.CharField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'ua_browser_version': ('django.db.models.fields.CharField', [], {'max_length': '20', 'null': 'True', 'blank': 'True'}),
            'ua_dist': ('django.db.models.fields.CharField', [], {'max_length': '20', 'null': 'True', 'blank': 'True'}),
            'ua_dist_version': ('django.db.models.fields.CharField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'ua_os': ('django.db.models.fields.CharField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'ua_os_version': ('django.db.models.fields.CharField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'updated': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'})
        },
        'dbmail.mailtemplate': {
            'Meta': {'object_name': 'MailTemplate'},
            'bcc_email': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'to': "orm['dbmail.MailBcc']", 'null': 'True', 'blank': 'True'}),
            'category': ('django.db.models.fields.related.ForeignKey', [], {'default': 'None', 'to': "orm['dbmail.MailCategory']", 'null': 'True', 'blank': 'True'}),
            'context_note': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'enable_log': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'from_email': ('django.db.models.fields.related.ForeignKey', [], {'default': 'None', 'to': "orm['dbmail.MailFromEmail']", 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'interval': ('django.db.models.fields.PositiveIntegerField', [], {'null': 'True', 'blank': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'is_admin': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_html': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'message': ('django.db.models.fields.TextField', [], {}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100', 'db_index': 'True'}),
            'num_of_retries': ('django.db.models.fields.PositiveIntegerField', [], {'default': '1'}),
            'priority': ('django.db.models.fields.SmallIntegerField', [], {'default': '6'}),
            'slug': ('django.db.models.fields.SlugField', [], {'unique': 'True', 'max_length': '50'}),
            'subject': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'updated': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'})
        },
        'dbmail.signal': {
            'Meta': {'object_name': 'Signal'},
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'group': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['dbmail.MailGroup']", 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'interval': ('django.db.models.fields.PositiveIntegerField', [], {'null': 'True', 'blank': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'model': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['contenttypes.ContentType']"}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'receive_once': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'rules': ('django.db.models.fields.TextField', [], {'default': "'{{ instance.email }}'", 'null': 'True', 'blank': 'True'}),
            'signal': ('django.db.models.fields.CharField', [], {'default': "'post_save'", 'max_length': '15'}),
            'template': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['dbmail.MailTemplate']"}),
            'update_model': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'updated': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'})
        },
        'dbmail.signaldeferreddispatch': {
            'Meta': {'object_name': 'SignalDeferredDispatch'},
            'args': ('django.db.models.fields.TextField', [], {}),
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'done': ('django.db.models.fields.NullBooleanField', [], {'default': 'None', 'null': 'True', 'blank': 'True'}),
            'eta': ('django.db.models.fields.DateTimeField', [], {'db_index': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'kwargs': ('django.db.models.fields.TextField', [], {}),
            'params': ('django.db.models.fields.TextField', [], {})
        },
        'dbmail.signallog': {
            'Meta': {'object_name': 'SignalLog'},
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['contenttypes.ContentType']"}),
            'model_pk': ('django.db.models.fields.BigIntegerField', [], {}),
            'signal': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['dbmail.Signal']"})
        }
    }

    complete_apps = ['dbmail']