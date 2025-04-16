# GRC/oreno/apps/core/admin.py
from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from django.conf import settings
from .middleware import get_current_organization

class TenantAdminSite(admin.AdminSite):
    """Custom admin site with multi-tenant awareness"""
    site_header = _("GRC Tenant Administration")
    site_title = _("GRC Tenant Portal")
    
    def get_app_list(self, request):
        """Customize app ordering for tenant admins"""
        app_list = super().get_app_list(request)
        ordering = {'organizations': 1, 'users': 2, 'core': 3}
        app_list.sort(key=lambda x: ordering.get(x['app_label'], 999))
        return app_list

class TenantModelAdmin(admin.ModelAdmin):
    """Base admin class for all tenant-aware models"""
    readonly_fields = ['organization', 'created_at', 'updated_at', 'created_by', 'updated_by']
    
    def get_queryset(self, request):
        """Filter queryset by current organization"""
        qs = super().get_queryset(request)
        org = get_current_organization()
        if org:
            return qs.filter(organization=org)
        return qs.none()  # Block access if no organization context

    def save_model(self, request, obj, form, change):
        """Automatically set organization and audit fields"""
        if not obj.organization_id:
            obj.organization = get_current_organization()
        if not change:  # New object
            obj.created_by = request.user
        obj.updated_by = request.user
        super().save_model(request, obj, form, change)

class BaseAuditAdmin(TenantModelAdmin):
    """Specialized admin for auditable models"""
    list_display = ['__str__', 'organization', 'created_at', 'created_by']
    list_filter = ['created_at', 'organization']
    search_fields = ['created_by__email', 'organization__name']

    def get_list_display(self, request):
        """Dynamically add audit fields if they exist"""
        display = list(self.list_display)
        if 'updated_at' in [f.name for f in self.model._meta.fields]:
            display.append('updated_at')
        return display

# Replace default admin site
admin_site = TenantAdminSite(name='tenant_admin')

# Example registration for core models (if any)
# @admin.register(SystemSetting, site=admin_site)
# class SystemSettingAdmin(BaseAuditAdmin):
#     list_display = BaseAuditAdmin.list_display + ['key', 'value']
#     search_fields = BaseAuditAdmin.search_fields + ['key']