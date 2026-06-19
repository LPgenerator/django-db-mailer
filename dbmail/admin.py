from __future__ import annotations

import os

from django import forms
from django.contrib import admin, messages
from django.contrib.contenttypes.models import ContentType
from django.shortcuts import redirect, render
from django.urls import re_path, reverse
from django.utils.translation import gettext_lazy as _

from dbmail import app_installed, defaults, get_model
from dbmail.models import (
    ApiKey,
    ApiKeyUsageAudit,
    MailBaseTemplate,
    MailBcc,
    MailCategory,
    MailFile,
    MailFromEmail,
    MailFromEmailCredential,
    MailGroup,
    MailGroupEmail,
    MailLog,
    MailLogEmail,
    MailLogException,
    MailLogTrack,
    MailSubscription,
    MailTemplate,
    Signal,
)

ModelAdmin = admin.ModelAdmin

if app_installed("reversion"):
    try:
        from reversion import VersionAdmin

        ModelAdmin = VersionAdmin
    except ImportError:
        pass

if app_installed("reversion_compare"):
    try:
        from reversion_compare.admin import CompareVersionAdmin

        ModelAdmin = CompareVersionAdmin
    except ImportError:
        pass

TranslationModelAdmin = ModelAdmin

if app_installed("modeltranslation"):
    if app_installed("grappelli_modeltranslation"):
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
    list_display = (
        "name",
        "created",
        "updated",
        "id",
    )
    list_filter = (
        "created",
        "updated",
    )
    search_fields = ("name",)


class MailTemplateFileAdmin(admin.TabularInline):
    model = MailFile
    extra = 1


class MailTemplateAdmin(TranslationModelAdmin):
    list_display = (
        "name",
        "category",
        "from_email",
        "slug",
        "is_admin",
        "is_html",
        "enable_log",
        "is_active",
        "num_of_retries",
        "priority",
        "created",
        "updated",
        "id",
    )
    list_filter = (
        "category",
        "is_active",
        "is_admin",
        "is_html",
        "priority",
        "from_email",
        "created",
        "updated",
    )
    search_fields = (
        "name",
        "subject",
        "slug",
        "message",
    )
    ordering = ("-id",)
    list_editable = (
        "category",
        "priority",
        "is_active",
    )
    filter_horizontal = ("bcc_email",)
    list_display_links = ("name",)
    date_hierarchy = "created"
    list_per_page = defaults.TEMPLATES_PER_PAGE
    inlines = [MailTemplateFileAdmin]
    prepopulated_fields = {"slug": ("name",)}

    class Media:
        js = ("dbmail/admin/js/dbmail.js",)

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("category", "from_email", "from_email__credential")

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "category":
            cached = getattr(request, "_dbmail_category_choices", None)
            if cached is None:
                cached = list(MailCategory.objects.all())
                request._dbmail_category_choices = cached
            kwargs.setdefault("queryset", db_field.related_model.objects.filter(pk__in=[obj.pk for obj in cached]))
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    def changelist_view(self, request, extra_context=None):
        self.change_list_template = "dbmail/admin/change_list_link.html"
        return super().changelist_view(request, extra_context=extra_context)

    def clean_cache_view(self, request):
        MailTemplate.clean_cache()
        ApiKey.clean_cache()
        messages.success(request, _("Cache was successful removed"))
        return redirect("admin:dbmail_mailtemplate_changelist")

    def send_mail_view(self, request, pk):
        from dbmail.management.commands.dbmail_test_send import send_test_msg

        if not request.user.email:
            messages.error(request, _("Set your email address in user settings."))
            return redirect(reverse("admin:dbmail_mailtemplate_change", args=(pk,), current_app=self.admin_site.name))

        try:
            send_test_msg(
                pk,
                request.user.email,
                use_celery=defaults.USE_CELERY_FOR_ADMIN_TEST,
                backend=defaults.BACKEND["mail"],
            )
        except Exception as exc:  # pragma: no cover - admin diagnostic path
            messages.error(request, _("Test send failed: %(exc)s") % {"exc": exc})
        else:
            messages.success(request, _("Email was sent to %(email)s.") % {"email": request.user.email})

        return redirect(reverse("admin:dbmail_mailtemplate_change", args=(pk,), current_app=self.admin_site.name))

    def get_apps_view(self, request, pk):
        apps_list = {}
        for ct in ContentType.objects.exclude(app_label__in=defaults.IGNORE_BROWSE_APP).order_by("app_label", "model"):
            if ct.model_class() is None:
                continue
            apps_list.setdefault(ct.app_label, []).append(ct)
        return render(request, "dbmail/apps.html", {"apps_list": apps_list})

    def browse_model_fields_view(self, request, pk, app, model):
        fields: dict[str, str] = {}
        try:
            model_class = get_model(app, model) if pk else None
        except LookupError:
            model_class = None
        if model_class is not None:
            for f in model_class._meta.fields:
                fields[f.name] = str(f.verbose_name)
        return render(request, "dbmail/browse.html", {"fields_list": fields})

    def get_urls(self):
        urls = super().get_urls()
        admin_urls = [
            re_path(r"^(?P<pk>\d+)/sendmail/$", self.admin_site.admin_view(self.send_mail_view), name="send_mail_view"),
            re_path(
                r"^(?P<pk>\d+)/sendmail/apps/(?P<app>[\w_]+)/(?P<model>[\w_]+)/?$",
                self.admin_site.admin_view(self.browse_model_fields_view),
                name="browse_model_fields_view",
            ),
            re_path(
                r"^(?P<pk>\d+)/sendmail/apps/?$",
                self.admin_site.admin_view(self.get_apps_view),
                name="send_mail_apps_view",
            ),
            re_path(r"^reset/cache/?$", self.admin_site.admin_view(self.clean_cache_view), name="clean_cache_view"),
        ]
        return admin_urls + urls

    def get_readonly_fields(self, request, obj=None):
        readonly = list(super().get_readonly_fields(request, obj))
        if obj is not None and defaults.READ_ONLY_ENABLED:
            readonly += ["slug", "context_note"]
        # SSTI guard: subject/message/from_email are rendered through
        # Django templates at send time, so a non-superuser editor could
        # leak settings via a context-walking gadget chain. Until the
        # sandboxed renderer lands, restrict these fields to superusers.
        user = getattr(request, "user", None)
        if user is None or not user.is_superuser:
            for field in ("subject", "message", "from_email"):
                if field not in readonly:
                    readonly.append(field)
        return readonly

    def get_prepopulated_fields(self, request, obj=None):
        if obj is not None:
            return {}
        return super().get_prepopulated_fields(request, obj)

    def has_add_permission(self, request) -> bool:
        # Adding a template means setting ``subject`` and ``message`` —
        # the SSTI vector. Same rationale as get_readonly_fields above.
        return bool(request.user and request.user.is_superuser)

    def get_queryset(self, request):
        return super(MailTemplateAdmin, self).get_queryset(request) \
            .select_related('from_email', 'category')

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        formfield = super(MailTemplateAdmin, self).formfield_for_foreignkey(
            db_field, request, **kwargs)
        if db_field.name == 'category':
            key = '_category_choices_cache'
            if not hasattr(request, key):
                setattr(request, key, list(formfield.choices))
            formfield.choices = getattr(request, key)
        return formfield


class MailLogEmailInline(admin.TabularInline):
    readonly_fields = [field.name for field in MailLogEmail._meta.fields]
    model = MailLogEmail
    extra = 0

    def has_add_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        if not request.user.is_superuser:
            return False
        return True

    def has_change_permission(self, request, obj=None):
        return request.method != "POST"


class MailLogAdmin(admin.ModelAdmin):
    list_display = (
        "template",
        "correlation_id",
        "created",
        "is_sent",
        "num_of_retries",
        "backend",
        "user",
        "id",
    )
    list_filter = (
        "is_sent",
        "backend",
        "created",
        "error_exception",
        "template",
    )
    date_hierarchy = "created"
    inlines = [MailLogEmailInline]
    search_fields = (
        "maillogemail__email",
        "user__username",
        "user__email",
        "correlation_id",
    )

    def __init__(self, model, admin_site):
        super().__init__(model, admin_site)

        self.readonly_fields = [field.name for field in model._meta.fields]
        self.readonly_model = model

    def has_add_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        if not request.user.is_superuser:
            return False
        return True

    def has_change_permission(self, request, obj=None):
        return request.method != "POST"


class MailGroupEmailInline(admin.TabularInline):
    model = MailGroupEmail
    extra = 1


class MailGroupAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "slug",
        "created",
        "updated",
        "id",
    )
    list_filter = (
        "updated",
        "created",
    )
    prepopulated_fields = {"slug": ("name",)}
    inlines = [MailGroupEmailInline]

    def get_readonly_fields(self, request, obj=None):
        if obj is not None and defaults.READ_ONLY_ENABLED:
            return ["slug"]
        return super().get_readonly_fields(request, obj)

    def get_prepopulated_fields(self, request, obj=None):
        if obj is not None:
            return {}
        return super().get_prepopulated_fields(request, obj)


class MailFromEmailAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "email",
        "credential",
        "created",
        "updated",
        "id",
    )
    list_filter = (
        "updated",
        "created",
    )


class SignalAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "model",
        "signal",
        "template",
        "interval",
        "receive_once",
        "is_active",
        "group",
        "updated",
        "created",
        "id",
    )
    list_filter = (
        "signal",
        "receive_once",
        "is_active",
        "update_model",
        "updated",
        "created",
    )
    list_editable = ("is_active",)

    @staticmethod
    def auto_reload(request):
        if defaults.WSGI_AUTO_RELOAD is True:
            env = request.environ.get
            if env("mod_wsgi.process_group") and env("SCRIPT_FILENAME"):
                if int(env("mod_wsgi.script_reloading", 0)):
                    try:
                        if os.path.exists(env("SCRIPT_FILENAME")):
                            os.utime(env("SCRIPT_FILENAME"), None)
                    except OSError:
                        pass

        if defaults.UWSGI_AUTO_RELOAD is True:
            try:
                import uwsgi

                uwsgi.reload()
            except ImportError:
                pass

    def save_model(self, request, *args, **kwargs):
        super().save_model(request, *args, **kwargs)
        self.auto_reload(request)

    def has_change_permission(self, request, obj=None) -> bool:
        # Signal.rules is rendered as a Django template against the
        # signalled instance. A staff editor with change_signal can
        # otherwise inject context-walking gadgets. Restrict edits to
        # superusers (or holders of an explicit dbmail.edit_signal_rules
        # perm) until the sandboxed engine lands in 3.1 — see
        # plan3/03-security-auditor.md SEC-C.
        if obj is None:
            return super().has_change_permission(request, obj)
        return bool(request.user and request.user.is_superuser)


class MailFromEmailCredentialForm(forms.ModelForm):
    """Hide SMTP password from admin change form rendering.

    The plain-text storage of ``password`` is documented as a known
    limitation in 3.0 (SECURITY.md); the column will move to an
    encrypted field in 3.1. Until then the admin must at least not
    leak the existing value through the change form HTML.
    """

    password = forms.CharField(
        label=_("Password"),
        required=False,
        widget=forms.PasswordInput(render_value=False),
        max_length=128,
        help_text=_("SMTP password or app-specific token. Leave blank to keep the existing value when editing."),
    )

    class Meta:
        model = MailFromEmailCredential
        fields = ("host", "port", "username", "password", "use_tls", "fail_silently")

    def clean_password(self) -> str | None:
        # Empty submission on edit means "keep current value".
        new = self.cleaned_data.get("password") or ""
        if not new and self.instance and self.instance.pk:
            return self.instance.password
        return new or None


class MailFromEmailCredentialAdmin(admin.ModelAdmin):
    form = MailFromEmailCredentialForm
    list_display = (
        "host",
        "port",
        "username",
        "use_tls",
        "fail_silently",
        "updated",
        "created",
        "id",
    )
    list_filter = (
        "use_tls",
        "fail_silently",
        "updated",
        "created",
    )

    @staticmethod
    def _is_superuser(request) -> bool:
        # SMTP credentials are sensitive; restrict to superusers per ADR
        # security recommendations until at-rest encryption ships in 3.1.
        return bool(request.user and request.user.is_superuser)

    def has_module_permission(self, request) -> bool:
        return self._is_superuser(request)

    def has_view_permission(self, request, obj=None) -> bool:
        return self._is_superuser(request)

    def has_add_permission(self, request) -> bool:
        return self._is_superuser(request)

    def has_change_permission(self, request, obj=None) -> bool:
        return self._is_superuser(request)

    def has_delete_permission(self, request, obj=None) -> bool:
        return self._is_superuser(request)


def _generate_api_key() -> str:
    import secrets

    return secrets.token_urlsafe(24)[:32]


class ApiKeyAdminForm(forms.ModelForm):
    api_key = forms.CharField(
        label=_("Api key"),
        required=False,
        max_length=32,
        help_text=_(
            "Leave blank to auto-generate a 32-char URL-safe key. The "
            "raw value is shown once on the success message after save."
        ),
    )

    class Meta:
        model = ApiKey
        fields = ("name", "api_key", "is_active")


class ApiKeyAdmin(admin.ModelAdmin):
    form = ApiKeyAdminForm
    list_display = (
        "name",
        "masked_api_key",
        "is_active",
        "last_used_at",
        "last_used_ip",
        "updated",
        "created",
        "id",
    )
    list_filter = (
        "is_active",
        "updated",
        "created",
    )
    search_fields = ("name",)

    def get_fieldsets(self, request, obj=None):
        if obj is None:
            return ((None, {"fields": ("name", "api_key", "is_active")}),)
        return (
            (None, {"fields": ("name", "is_active")}),
            (
                _("Credential"),
                {
                    "fields": ("api_key_display", "password_hash_display"),
                    "description": _("API keys are hashed on save. Use admin actions to rotate or revoke."),
                },
            ),
            (
                _("Audit"),
                {
                    "fields": ("last_used_at", "last_used_ip", "created", "updated"),
                },
            ),
        )

    def get_readonly_fields(self, request, obj=None):
        if obj is None:
            return ()
        return (
            "api_key_display",
            "password_hash_display",
            "last_used_at",
            "last_used_ip",
            "created",
            "updated",
        )

    @admin.display(description=_("Api key"))
    def masked_api_key(self, obj: ApiKey) -> str:
        if not obj.api_key:
            return "—"
        if len(obj.api_key) <= 6:
            return "•" * len(obj.api_key)
        return obj.api_key[:4] + "…" + obj.api_key[-2:]

    @admin.display(description=_("Api key"))
    def api_key_display(self, obj: ApiKey) -> str:
        return self.masked_api_key(obj)

    @admin.display(description=_("Password hash"))
    def password_hash_display(self, obj: ApiKey) -> str:
        if not obj.password_hash:
            return _("(not yet hashed — will populate on next save)")
        algo = obj.password_hash.split("$", 1)[0] if "$" in obj.password_hash else "?"
        return _("%(algo)s — set ✓") % {"algo": algo}

    def save_model(self, request, obj: ApiKey, form, change) -> None:
        raw = form.cleaned_data.get("api_key") or ""
        if not change and not raw:
            raw = _generate_api_key()
            obj.api_key = raw
            messages.success(
                request,
                _("Api key created. Copy this value now, it will be masked after this page reloads: %(raw)s")
                % {"raw": raw},
            )
        elif raw and raw != obj.api_key:
            obj.api_key = raw
            obj.password_hash = ""
        super().save_model(request, obj, form, change)

    actions = ("rotate_api_key", "revoke_api_key")

    @admin.action(description=_("Rotate selected API keys"))
    def rotate_api_key(self, request, queryset):
        rotated: list[str] = []
        for obj in queryset:
            new_key = _generate_api_key()
            obj.api_key = new_key
            obj.password_hash = ""
            obj.save()
            rotated.append(f"{obj.name}: {new_key}")
        messages.success(
            request,
            _("Rotated %(count)d key(s). New raw values: %(values)s")
            % {"count": len(rotated), "values": "; ".join(rotated)},
        )

    @admin.action(description=_("Revoke selected API keys"))
    def revoke_api_key(self, request, queryset):
        count = queryset.update(is_active=False)
        messages.success(request, _("Revoked %(count)d key(s).") % {"count": count})


class MailBccAdmin(admin.ModelAdmin):
    list_display = (
        "email",
        "is_active",
        "updated",
        "created",
        "id",
    )
    list_filter = (
        "is_active",
        "updated",
        "created",
    )


class MailLogTrackAdmin(admin.ModelAdmin):
    list_display = (
        "mail_log",
        "counter",
        "ip",
        "is_read",
        "updated",
        "created",
        "id",
    )

    def __init__(self, model, admin_site):
        super().__init__(model, admin_site)

        self.readonly_fields = [field.name for field in model._meta.fields]
        self.readonly_model = model

    def has_add_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        if not request.user.is_superuser:
            return False
        return True

    def has_change_permission(self, request, obj=None):
        return request.method != "POST"


class MailBaseTemplateAdmin(TranslationModelAdmin):
    list_display = (
        "name",
        "created",
        "updated",
        "id",
    )
    list_filter = (
        "created",
        "updated",
    )
    search_fields = ("name", "message")

    def get_readonly_fields(self, request, obj=None):
        # Same SSTI surface as MailTemplate.message — the base template
        # is concatenated with the per-template body before
        # ``Template().render(Context())`` runs. Restrict edits to
        # superusers / dbmail.edit_template_body.
        readonly = list(super().get_readonly_fields(request, obj))
        user = getattr(request, "user", None)
        if user is None or not user.is_superuser:
            if "message" not in readonly:
                readonly.append("message")
        return readonly

    def has_add_permission(self, request) -> bool:
        return bool(request.user and request.user.is_superuser)


class MailSubscriptionAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "address",
        "backend",
        "start_hour",
        "end_hour",
        "is_enabled",
        "is_checked",
        "defer_at_allowed_hours",
        "id",
    )
    list_filter = ("backend", "is_enabled", "is_checked", "defer_at_allowed_hours")
    search_fields = ("user__name", "user__email", "address")


class MailLogExceptionAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "ignore",
        "id",
    )
    list_filter = ("ignore",)
    search_fields = ("name",)
    readonly_fields = ("name",)

    def has_add_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        if not request.user.is_superuser:
            return False
        return True


class ApiKeyUsageAuditAdmin(admin.ModelAdmin):
    """Read-only audit log; rows are produced by ``send_by_dbmail``."""

    list_display = ("created", "action", "api_key_name", "success", "ip", "id")
    list_filter = ("action", "success", "created")
    search_fields = ("api_key_name", "ip", "detail")
    readonly_fields = tuple(f.name for f in ApiKeyUsageAudit._meta.fields)
    date_hierarchy = "created"

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False


def admin_register(model):
    model_name = model.__name__
    if model_name in defaults.ALLOWED_MODELS_ON_ADMIN:
        admin_cls = globals().get("%sAdmin" % model_name)
        if admin_cls:
            admin.site.register(model, admin_cls)
        else:
            admin.site.register(model)


admin_register(MailFromEmailCredential)
admin_register(MailSubscription)
admin_register(MailBaseTemplate)
admin_register(MailLogException)
admin_register(MailFromEmail)
admin_register(MailLogTrack)
admin_register(MailCategory)
admin_register(MailTemplate)
admin_register(MailGroup)
admin_register(MailLog)
admin_register(MailBcc)
admin_register(Signal)
admin_register(ApiKey)
admin_register(ApiKeyUsageAudit)
