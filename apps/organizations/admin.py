# apps/organizations/admin.py

from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from django_tenants.admin import TenantAdminMixin
from reversion.admin import VersionAdmin
from .models import Organization, OrganizationSettings, Subscription, Domain
from django import forms

@admin.register(Organization)
class OrganizationAdmin(TenantAdminMixin, VersionAdmin):
    """
    Admin for tenant Organizations with enhanced security and privacy controls.
    """
    list_display = (
        'name',
        'code',
        'is_active',
        'created_at',
    )
    list_filter = (
        'is_active',
        'created_at',
    )
    search_fields = (
        'name',
        'code',
        'description',
    )
    readonly_fields = (
        'created_at',
        'updated_at',
    )
    fieldsets = (
        (None, {
            'fields': ('name', 'code', 'is_active')
        }),
        (_('Details'), {
            'fields': ('description', 'website', 'logo')
        }),
        (_('System Information'), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    actions = ['deactivate_organizations', 'archive_organizations']

    def get_queryset(self, request):
        return super().get_queryset(request)

    def has_change_permission(self, request, obj=None):
        if not obj:
            return True
        return request.user.is_superuser or (
            request.user.is_authenticated and
            request.user.organization == obj and
            request.user.role == 'admin'
        )

    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser

    def deactivate_organizations(self, request, queryset):
        queryset.update(is_active=False)
    deactivate_organizations.short_description = _("Deactivate selected organizations")

    def archive_organizations(self, request, queryset):
        for org in queryset:
            org.archive()
    archive_organizations.short_description = _("Archive selected organizations")

class OrganizationSettingsAdminForm(forms.ModelForm):
    APP_CHOICES = [
        ('audit', 'Audit'),
        ('risk', 'Risk'),
        ('legal', 'Legal'),
        ('compliance', 'Compliance'),
        ('contracts', 'Contracts'),
        ('document_management', 'Document Management'),
    ]
    subscribed_apps = forms.MultipleChoiceField(
        choices=APP_CHOICES,
        required=False,
        widget=forms.CheckboxSelectMultiple,
        label='Subscribed Apps',
        help_text='Select which apps this organization can access.'
    )
    class Meta:
        model = OrganizationSettings
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Set initial value from JSONField
        if self.instance and self.instance.pk:
            self.fields['subscribed_apps'].initial = self.instance.subscribed_apps

    def clean_subscribed_apps(self):
        return self.cleaned_data['subscribed_apps']

    def save(self, commit=True):
        instance = super().save(commit=False)
        instance.subscribed_apps = self.cleaned_data['subscribed_apps']
        if commit:
            instance.save()
        return instance

@admin.register(OrganizationSettings)
class OrganizationSettingsAdmin(VersionAdmin):
    form = OrganizationSettingsAdminForm
    list_display = ('organization', 'subscription_plan', 'is_active')
    list_filter = ('subscription_plan', 'is_active')
    filter_horizontal = ()
    def get_readonly_fields(self, request, obj=None):
        if obj:  # editing existing
            return ('organization',)
        return ()
    def has_change_permission(self, request, obj=None):
        if not obj:
            return True
        return request.user.is_superuser or (
            request.user.is_authenticated and
            request.user.organization == obj.organization and
            request.user.role == 'admin'
        )

@admin.register(Subscription)
class SubscriptionAdmin(VersionAdmin):
    list_display = ('organization', 'subscription_plan', 'status', 'start_date', 'end_date')
    list_filter = ('subscription_plan', 'status', 'billing_cycle')

    def get_readonly_fields(self, request, obj=None):
        if obj:  # editing existing
            return ('organization',)
        return ()

    def has_change_permission(self, request, obj=None):
        if not obj:
            return True
        return request.user.is_superuser or (
            request.user.is_authenticated and
            request.user.organization == obj.organization and
            request.user.role == 'admin'
        )

@admin.register(Domain)
class DomainAdmin(VersionAdmin):
    list_display = ('domain', 'tenant', 'is_primary', 'created_at')
    list_filter = ('is_primary', 'created_at')
    search_fields = ('domain', 'tenant__name')

    def has_change_permission(self, request, obj=None):
        if not obj:
            return True
        return request.user.is_superuser or (
            request.user.is_authenticated and
            request.user.organization == obj.tenant and
            request.user.role == 'admin'
        )
