# -*- coding: utf-8 -*-

import re

from django.shortcuts import redirect, render
from django.core.urlresolvers import reverse
from django.conf.urls import patterns, url
from django.contrib import admin
from django.conf import settings

from django.contrib.contenttypes.models import ContentType
from django.db.models import get_model

from dbmail.models import (
    MailCategory, MailTemplate, MailLog, MailLogEmail, Signal,
    MailGroup, MailGroupEmail, MailFile, MailFromEmail, MailFromEmailCredential
)
from dbmail import send_db_mail
from dbmail import defaults


ModelAdmin = admin.ModelAdmin

if 'reversion' in settings.INSTALLED_APPS:
    try:
        from reversion import VersionAdmin

        ModelAdmin = VersionAdmin
    except ImportError:
        pass


class MailCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'created', 'updated', 'id',)
    list_filter = ('created', 'updated',)
    search_fields = ('name',)


class MailTemplateFileAdmin(admin.TabularInline):
    model = MailFile
    extra = 1


class MailTemplateAdmin(ModelAdmin):
    list_display = (
        'name', 'category', 'from_email', 'slug', 'is_admin', 'is_html',
        'num_of_retries', 'priority', 'created', 'updated', 'id',
    )
    list_filter = (
        'category', 'is_admin', 'is_html', 'priority',
        'from_email', 'created', 'updated',)
    search_fields = (
        'name', 'subject', 'slug', 'message',)
    prepopulated_fields = {'slug': ('name',)}
    ordering = ('-id',)
    list_editable = ('category', 'priority',)
    list_display_links = ('name',)
    date_hierarchy = 'created'
    list_per_page = defaults.TEMPLATES_PER_PAGE
    inlines = [MailTemplateFileAdmin]

    class Media:
        js = (
            '/static/dbmail/admin/js/dbmail.js',
        )

    def send_mail_view(self, request, pk):
        template = MailTemplate.objects.get(pk=pk)
        slug = template.slug
        var_list = re.findall('\{\{\s?(\w+)\s?\}\}', template.message)
        context = {}
        for var in var_list:
            context[var] = '"%s"' % var.upper().replace('_', '-')
        send_db_mail(slug, request.user.email, request.user, context)
        return redirect(
            reverse(
                'admin:dbmail_mailtemplate_change', args=(pk,),
                current_app=self.admin_site.name
            )
        )

    def get_apps_view(self, request, pk):
        apps_list = {}
        for ct in ContentType.objects.all():
            if ct.app_label not in apps_list:
                apps_list[ct.app_label] = [ct]
            else:
                apps_list[ct.app_label].append(ct)
        return render(request, 'dbmail/apps.html', {'apps_list': apps_list})

    def browse_model_fields_view(self, request, pk, app, model):
        fields = dict()
        for f in get_model(app, model)._meta.fields:
            fields[f.name] = unicode(f.verbose_name)
        return render(request, 'dbmail/browse.html', {'fields_list': fields})

    def get_urls(self):
        urls = super(MailTemplateAdmin, self).get_urls()
        admin_urls = patterns(
            '',
            url(
                r'^(\d+)/sendmail/$',
                self.admin_site.admin_view(self.send_mail_view),
                name='send_mail_view'
            ),
            url(
                r'^(\d+)/sendmail/apps/(.*?)/(.*?)/',
                self.admin_site.admin_view(self.browse_model_fields_view),
                name='browse_model_fields_view'),
            url(
                r'^(\d+)/sendmail/apps/',
                self.admin_site.admin_view(self.get_apps_view),
                name='send_mail_apps_view'
            ),
        )
        return admin_urls + urls

    def get_readonly_fields(self, request, obj=None):
        if obj is not None and defaults.READ_ONLY_ENABLED:
            return ['slug', 'context_note']
        return self.readonly_fields

    def get_prepopulated_fields(self, request, obj=None):
        if obj is not None:
            return {}
        return self.prepopulated_fields


class MailLogEmailInline(admin.TabularInline):
    readonly_fields = [field.name for field in MailLogEmail._meta.fields]
    model = MailLogEmail
    extra = 0

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return request.method != 'POST'


class MailLogAdmin(admin.ModelAdmin):
    list_display = (
        'template', 'created', 'is_sent', 'num_of_retries', 'user', 'id',)
    list_filter = ('is_sent', 'created',)
    date_hierarchy = 'created'
    inlines = [MailLogEmailInline]

    def __init__(self, model, admin_site):
        super(MailLogAdmin, self).__init__(model, admin_site)

        self.readonly_fields = [field.name for field in model._meta.fields]
        self.readonly_model = model

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return request.method != 'POST'


class MailGroupEmailInline(admin.TabularInline):
    model = MailGroupEmail
    extra = 1


class MailGroupAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'created', 'updated', 'id',)
    list_filter = ('updated', 'created',)
    prepopulated_fields = {'slug': ('name',)}
    inlines = [MailGroupEmailInline]

    def get_readonly_fields(self, request, obj=None):
        if obj is not None and defaults.READ_ONLY_ENABLED:
            return ['slug']
        return self.readonly_fields

    def get_prepopulated_fields(self, request, obj=None):
        if obj is not None:
            return {}
        return self.prepopulated_fields


class MailFromEmailAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'credential', 'created', 'updated', 'id',)
    list_filter = ('updated', 'created',)


class SignalAdmin(admin.ModelAdmin):
    list_display = (
        'name', 'model', 'signal', 'template', 'interval', 'receive_once',
        'updated', 'created', 'id',)
    list_filter = ('signal', 'receive_once', 'updated', 'created',)


class MailFromEmailCredentialAdmin(admin.ModelAdmin):
    list_display = (
        'host', 'port', 'username', 'use_tls',
        'fail_silently', 'updated', 'created', 'id',)
    list_filter = ('use_tls', 'fail_silently', 'updated', 'created',)


admin.site.register(MailFromEmailCredential, MailFromEmailCredentialAdmin)
admin.site.register(MailFromEmail, MailFromEmailAdmin)
admin.site.register(MailCategory, MailCategoryAdmin)
admin.site.register(MailTemplate, MailTemplateAdmin)
admin.site.register(MailLog, MailLogAdmin)
admin.site.register(MailGroup, MailGroupAdmin)
admin.site.register(Signal, SignalAdmin)
