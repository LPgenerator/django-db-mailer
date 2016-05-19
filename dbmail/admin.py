# -*- coding: utf-8 -*-

import os

from django.contrib.contenttypes.models import ContentType
from django.utils.translation import ugettext_lazy as _
from django.shortcuts import redirect, render
from django.core.urlresolvers import reverse
from django.conf.urls import patterns, url
from django.contrib import messages
from django.contrib import admin

from dbmail.models import (
    MailCategory, MailTemplate, MailLog, MailLogEmail, Signal, ApiKey, MailBcc,
    MailGroup, MailGroupEmail, MailFile, MailFromEmail, MailBaseTemplate,
    MailFromEmailCredential, MailLogTrack, MailSubscription
)
from dbmail import app_installed
from dbmail import get_model
from dbmail import defaults

ModelAdmin = admin.ModelAdmin

if app_installed('reversion'):
    try:
        from reversion import VersionAdmin

        ModelAdmin = VersionAdmin
    except ImportError:
        pass

if app_installed('reversion_compare'):
    try:
        from reversion_compare.admin import CompareVersionAdmin

        ModelAdmin = CompareVersionAdmin
    except ImportError:
        pass

TranslationModelAdmin = ModelAdmin

if app_installed('modeltranslation'):
    if app_installed('grappelli_modeltranslation'):
        try:
            from grappelli_modeltranslation.admin import TranslationAdmin

            class TranslationModelAdmin(ModelAdmin, TranslationAdmin):
                pass
        except ImportError:
            pass
    else:
        try:
            from modeltranslation.admin import TabbedTranslationAdmin

            class TranslationModelAdmin(TabbedTranslationAdmin, ModelAdmin):
                pass
        except ImportError:
            pass


class MailCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'created', 'updated', 'id',)
    list_filter = ('created', 'updated',)
    search_fields = ('name',)


class MailTemplateFileAdmin(admin.TabularInline):
    model = MailFile
    extra = 1


class MailTemplateAdmin(TranslationModelAdmin):
    list_display = (
        'name', 'category', 'from_email', 'slug', 'is_admin', 'is_html',
        'enable_log', 'is_active', 'num_of_retries', 'priority',
        'created', 'updated', 'id',
    )
    list_filter = (
        'category', 'is_active', 'is_admin', 'is_html', 'priority',
        'from_email', 'created', 'updated',)
    search_fields = (
        'name', 'subject', 'slug', 'message',)
    ordering = ('-id',)
    list_editable = ('category', 'priority', 'is_active',)
    filter_horizontal = ('bcc_email',)
    list_display_links = ('name',)
    date_hierarchy = 'created'
    list_per_page = defaults.TEMPLATES_PER_PAGE
    inlines = [MailTemplateFileAdmin]
    prepopulated_fields = {'slug': ('name',)}

    class Media:
        js = (
            'dbmail/admin/js/dbmail.js',
        )

    def changelist_view(self, request, extra_context=None):
        self.change_list_template = 'dbmail/admin/change_list_link.html'
        return super(MailTemplateAdmin, self).changelist_view(
            request, extra_context=extra_context)

    def clean_cache_view(self, request):
        MailTemplate.clean_cache()
        ApiKey.clean_cache()
        messages.success(request, _('Cache was successful removed'))
        return redirect('admin:dbmail_mailtemplate_changelist')

    def send_mail_view(self, request, pk):
        from dbmail.management.commands.dbmail_test_send import send_test_msg

        if request.user.email:
            send_test_msg(
                pk, request.user.email, request.user,
                use_celery=defaults.USE_CELERY_FOR_ADMIN_TEST,
                backend=defaults.BACKEND['mail'])
            messages.success(request, _('Email was sent.'))
        else:
            messages.error(
                request, _('Set your email address in user settings.')
            )

        return redirect(
            reverse(
                'admin:dbmail_mailtemplate_change', args=(pk,),
                current_app=self.admin_site.name
            )
        )

    def get_apps_view(self, request, pk):
        apps_list = {}
        for ct in ContentType.objects.all():
            if ct.app_label in defaults.IGNORE_BROWSE_APP:
                continue
            if ct.app_label not in apps_list:
                apps_list[ct.app_label] = [ct]
            elif ct.model_class():
                apps_list[ct.app_label].append(ct)
        return render(request, 'dbmail/apps.html', {'apps_list': apps_list})

    def browse_model_fields_view(self, request, pk, app, model):
        fields = dict()
        if pk and get_model(app, model):
            for f in get_model(app, model)._meta.fields:
                try:
                    fields[f.name] = unicode(f.verbose_name)
                except NameError:
                    fields[f.name] = f.verbose_name
        return render(request, 'dbmail/browse.html', {'fields_list': fields})

    def get_urls(self):
        urls = super(MailTemplateAdmin, self).get_urls()
        admin_urls = [
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
            url(
                r'^reset/cache/',
                self.admin_site.admin_view(self.clean_cache_view),
                name='clean_cache_view'
            ),
        ]
        return admin_urls + urls

    def get_readonly_fields(self, request, obj=None):
        if obj is not None and defaults.READ_ONLY_ENABLED:
            return ['slug', 'context_note']
        return super(MailTemplateAdmin, self).get_readonly_fields(request, obj)

    def get_prepopulated_fields(self, request, obj=None):
        if obj is not None:
            return {}
        return super(MailTemplateAdmin, self).get_prepopulated_fields(
            request, obj)


class MailLogEmailInline(admin.TabularInline):
    readonly_fields = [field.name for field in MailLogEmail._meta.fields]
    model = MailLogEmail
    extra = 0

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        if not request.user.is_superuser:
            return False
        return True

    def has_change_permission(self, request, obj=None):
        return request.method != 'POST'


class MailLogAdmin(admin.ModelAdmin):
    list_display = (
        'template', 'created', 'is_sent', 'num_of_retries',
        'backend', 'user', 'id',)
    list_filter = (
        'is_sent', 'backend', 'created', 'error_exception', 'template',)
    date_hierarchy = 'created'
    inlines = [MailLogEmailInline]
    search_fields = ('maillogemail__email', 'user__username', 'user__email',)

    def __init__(self, model, admin_site):
        super(MailLogAdmin, self).__init__(model, admin_site)

        self.readonly_fields = [field.name for field in model._meta.fields]
        self.readonly_model = model

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        if not request.user.is_superuser:
            return False
        return True

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
        return super(MailGroupAdmin, self).get_readonly_fields(request, obj)

    def get_prepopulated_fields(self, request, obj=None):
        if obj is not None:
            return {}
        return super(MailGroupAdmin, self).get_prepopulated_fields(
            request, obj)


class MailFromEmailAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'credential', 'created', 'updated', 'id',)
    list_filter = ('updated', 'created',)


class SignalAdmin(admin.ModelAdmin):
    list_display = (
        'name', 'model', 'signal', 'template', 'interval', 'receive_once',
        'is_active', 'group', 'updated', 'created', 'id',)
    list_filter = (
        'signal', 'receive_once', 'is_active',
        'update_model', 'updated', 'created',)
    list_editable = ('is_active',)

    @staticmethod
    def auto_reload(request):
        if defaults.WSGI_AUTO_RELOAD is True:
            env = request.environ.get
            if env('mod_wsgi.process_group') and env('SCRIPT_FILENAME'):
                if int(env('mod_wsgi.script_reloading', 0)):
                    try:
                        if os.path.exists(env('SCRIPT_FILENAME')):
                            os.utime(env('SCRIPT_FILENAME'), None)
                    except OSError:
                        pass

        if defaults.UWSGI_AUTO_RELOAD is True:
            try:
                import uwsgi

                uwsgi.reload()
            except ImportError:
                pass

    def save_model(self, request, *args, **kwargs):
        super(SignalAdmin, self).save_model(request, *args, **kwargs)
        self.auto_reload(request)


class MailFromEmailCredentialAdmin(admin.ModelAdmin):
    list_display = (
        'host', 'port', 'username', 'use_tls',
        'fail_silently', 'updated', 'created', 'id',)
    list_filter = ('use_tls', 'fail_silently', 'updated', 'created',)


class ApiKeyAdmin(admin.ModelAdmin):
    list_display = (
        'name', 'api_key', 'is_active', 'updated', 'created', 'id',)
    list_filter = ('is_active', 'updated', 'created',)


class MailBccAdmin(admin.ModelAdmin):
    list_display = (
        'email', 'is_active', 'updated', 'created', 'id',)
    list_filter = ('is_active', 'updated', 'created',)


class MailLogTrackAdmin(admin.ModelAdmin):
    list_display = (
        'mail_log', 'counter', 'ip', 'is_read', 'updated', 'created', 'id',)

    def __init__(self, model, admin_site):
        super(MailLogTrackAdmin, self).__init__(model, admin_site)

        self.readonly_fields = [field.name for field in model._meta.fields]
        self.readonly_model = model

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        if not request.user.is_superuser:
            return False
        return True

    def has_change_permission(self, request, obj=None):
        return request.method != 'POST'


class MailBaseTemplateAdmin(TranslationModelAdmin):
    list_display = ('name', 'created', 'updated', 'id',)
    list_filter = ('created', 'updated',)
    search_fields = ('name', 'message')


class MailSubscriptionAdmin(admin.ModelAdmin):
    list_display = (
        'user', 'address', 'backend', 'start_hour', 'end_hour',
        'is_enabled', 'is_checked', 'defer_at_allowed_hours',
        'id',
    )
    list_filter = (
        'backend', 'is_enabled', 'is_checked', 'defer_at_allowed_hours')
    search_fields = (
        'user__name', 'user__email', 'address')


def admin_register(model):
    model_name = model.__name__
    if model_name in defaults.ALLOWED_MODELS_ON_ADMIN:
        admin_cls = globals().get('%sAdmin' % model_name)
        if admin_cls:
            admin.site.register(model, admin_cls)
        else:
            admin.site.register(model)


admin_register(MailFromEmailCredential)
admin_register(MailSubscription)
admin_register(MailBaseTemplate)
admin_register(MailFromEmail)
admin_register(MailLogTrack)
admin_register(MailCategory)
admin_register(MailTemplate)
admin_register(MailGroup)
admin_register(MailLog)
admin_register(MailBcc)
admin_register(Signal)
admin_register(ApiKey)
