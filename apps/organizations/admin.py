# apps/organizations/admin.py

from django.contrib import admin
from django_tenants.admin import TenantAdminMixin

from .models import (
    Organization,
    ArchivedOrganization,
    OrganizationSettings,
    Subscription,
    Domain,
)

@admin.register(Organization)
class OrganizationAdmin(TenantAdminMixin, admin.ModelAdmin):
    """
    Admin for tenant Organizations.  We display:
      - customer_name
      - customer_code
      - is_active
      - primary custom domain (via the Domain model)
    """
    list_display = (
        'customer_name',
        'customer_code',
        'is_active',
        'primary_domain',   # <— this method replaces the old custom_domain field
    )
    list_filter = ('is_active', 'customer_industry')
    search_fields = ('customer_name', 'customer_code', 'customer_industry')

    def primary_domain(self, obj):
        """
        Look up the Domain record marked is_primary for this tenant.
        Returns its hostname or empty string if none.
        """
        primary = Domain.objects.filter(tenant=obj, is_primary=True).first()
        return primary.domain if primary else ''
    primary_domain.short_description = 'Custom Domain'

# Register the rest of your models
admin.site.register(ArchivedOrganization)
admin.site.register(OrganizationSettings)
admin.site.register(Subscription)
admin.site.register(Domain)
