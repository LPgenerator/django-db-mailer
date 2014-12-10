# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models
from django import VERSION


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'SignalDeferredDispatch'
        db.create_table(u'dbmail_signaldeferreddispatch', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('args', self.gf('django.db.models.fields.TextField')()),
            ('kwargs', self.gf('django.db.models.fields.TextField')()),
            ('params', self.gf('django.db.models.fields.TextField')()),
            ('eta', self.gf('django.db.models.fields.DateTimeField')(db_index=True)),
            ('done', self.gf('django.db.models.fields.NullBooleanField')(default=None, null=True, blank=True)),
            ('created', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
        ))
        db.send_create_signal(u'dbmail', ['SignalDeferredDispatch'])

        # Adding index on 'SignalDeferredDispatch', fields ['eta', 'done']
        db.create_index(u'dbmail_signaldeferreddispatch', ['eta', 'done'])


    def backwards(self, orm):
        # Removing index on 'SignalDeferredDispatch', fields ['eta', 'done']
        db.delete_index(u'dbmail_signaldeferreddispatch', ['eta', 'done'])

        # Deleting model 'SignalDeferredDispatch'
        db.delete_table(u'dbmail_signaldeferreddispatch')


    models = {
        u'auth.group': {
            'Meta': {'object_name': 'Group'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '80'}),
            'permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'})
        },
        u'auth.permission': {
            'Meta': {'ordering': "(u'content_type__app_label', u'content_type__model', u'codename')", 'unique_together': "((u'content_type', u'codename'),)", 'object_name': 'Permission'},
            'codename': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['contenttypes.ContentType']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        u'auth.user': {
            'Meta': {'object_name': 'User'},
            'date_joined': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75', 'blank': 'True'}),
            'first_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'groups': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['auth.Group']", 'symmetrical': 'False', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'is_staff': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_superuser': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'last_login': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'last_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'user_permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'}),
            'username': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '30'})
        },
        u'contenttypes.contenttype': {
            'Meta': {'ordering': "('name',)", 'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        u'dbmail.apikey': {
            'Meta': {'object_name': 'ApiKey'},
            'api_key': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '32'}),
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '25'}),
            'updated': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'})
        },
        u'dbmail.mailbcc': {
            'Meta': {'object_name': 'MailBcc'},
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'email': ('django.db.models.fields.EmailField', [], {'unique': 'True', 'max_length': '75'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'updated': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'})
        },
        u'dbmail.mailcategory': {
            'Meta': {'object_name': 'MailCategory'},
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '25'}),
            'updated': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'})
        },
        u'dbmail.mailfile': {
            'Meta': {'object_name': 'MailFile'},
            'filename': ('django.db.models.fields.files.FileField', [], {'max_length': '100'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'template': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'files'", 'to': u"orm['dbmail.MailTemplate']"})
        },
        u'dbmail.mailfromemail': {
            'Meta': {'object_name': 'MailFromEmail'},
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'credential': ('django.db.models.fields.related.ForeignKey', [], {'default': 'None', 'to': u"orm['dbmail.MailFromEmailCredential']", 'null': 'True', 'blank': 'True'}),
            'email': ('django.db.models.fields.EmailField', [], {'unique': 'True', 'max_length': '75'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'updated': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'})
        },
        u'dbmail.mailfromemailcredential': {
            'Meta': {'object_name': 'MailFromEmailCredential'},
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'fail_silently': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'host': ('django.db.models.fields.CharField', [], {'max_length': '50'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '50', 'null': 'True', 'blank': 'True'}),
            'port': ('django.db.models.fields.PositiveIntegerField', [], {}),
            'updated': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'use_tls': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'username': ('django.db.models.fields.CharField', [], {'max_length': '50', 'null': 'True', 'blank': 'True'})
        },
        u'dbmail.mailgroup': {
            'Meta': {'object_name': 'MailGroup'},
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'slug': ('django.db.models.fields.SlugField', [], {'unique': 'True', 'max_length': '50'}),
            'updated': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'})
        },
        u'dbmail.mailgroupemail': {
            'Meta': {'unique_together': "(('email', 'group'),)", 'object_name': 'MailGroupEmail'},
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75'}),
            'group': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'emails'", 'to': u"orm['dbmail.MailGroup']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        u'dbmail.maillog': {
            'Meta': {'object_name': 'MailLog'},
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'error_exception': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['dbmail.MailLogException']", 'null': 'True', 'blank': 'True'}),
            'error_message': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_sent': ('django.db.models.fields.BooleanField', [], {'default': 'True', 'db_index': 'True'}),
            'num_of_retries': ('django.db.models.fields.PositiveIntegerField', [], {'default': '1'}),
            'template': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['dbmail.MailTemplate']"}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['auth.User']", 'null': 'True', 'blank': 'True'})
        },
        u'dbmail.maillogemail': {
            'Meta': {'object_name': 'MailLogEmail'},
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'log': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['dbmail.MailLog']"}),
            'mail_type': ('django.db.models.fields.CharField', [], {'max_length': '3'})
        },
        u'dbmail.maillogexception': {
            'Meta': {'object_name': 'MailLogException'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '150'})
        },
        u'dbmail.mailtemplate': {
            'Meta': {'object_name': 'MailTemplate'},
            'bcc_email': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'to': u"orm['dbmail.MailBcc']", 'null': 'True', 'blank': 'True'}),
            'category': ('django.db.models.fields.related.ForeignKey', [], {'default': 'None', 'to': u"orm['dbmail.MailCategory']", 'null': 'True', 'blank': 'True'}),
            'context_note': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'enable_log': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'from_email': ('django.db.models.fields.related.ForeignKey', [], {'default': 'None', 'to': u"orm['dbmail.MailFromEmail']", 'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
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
        u'dbmail.signal': {
            'Meta': {'object_name': 'Signal'},
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'group': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['dbmail.MailGroup']", 'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'interval': ('django.db.models.fields.PositiveIntegerField', [], {'null': 'True', 'blank': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'model': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['contenttypes.ContentType']"}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'receive_once': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'rules': ('django.db.models.fields.TextField', [], {'default': "'{{ instance.email }}'", 'null': 'True', 'blank': 'True'}),
            'signal': ('django.db.models.fields.CharField', [], {'default': "'post_save'", 'max_length': '15'}),
            'template': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['dbmail.MailTemplate']"}),
            'update_model': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'updated': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'})
        },
        u'dbmail.signaldeferreddispatch': {
            #'Meta': {'object_name': 'SignalDeferredDispatch', 'index_together': "(('eta', 'done'),)"},
            'args': ('django.db.models.fields.TextField', [], {}),
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'done': ('django.db.models.fields.NullBooleanField', [], {'default': 'None', 'null': 'True', 'blank': 'True'}),
            'eta': ('django.db.models.fields.DateTimeField', [], {'db_index': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'kwargs': ('django.db.models.fields.TextField', [], {}),
            'params': ('django.db.models.fields.TextField', [], {})
        },
        u'dbmail.signallog': {
            'Meta': {'object_name': 'SignalLog'},
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['contenttypes.ContentType']"}),
            'model_pk': ('django.db.models.fields.BigIntegerField', [], {}),
            'signal': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['dbmail.Signal']"})
        }
    }

    if VERSION >= (1, 5):
        models[u'dbmail.signaldeferreddispatch']['Meta'] = {'object_name': 'SignalDeferredDispatch', 'index_together': "(('eta', 'done'),)"}
    else:
        models[u'dbmail.signaldeferreddispatch']['Meta'] = {'object_name': 'SignalDeferredDispatch'}

    complete_apps = ['dbmail']
