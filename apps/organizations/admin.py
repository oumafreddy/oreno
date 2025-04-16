from django.contrib import admin
from .models import Organization, ArchivedOrganization, OrganizationSettings, Subscription

admin.site.register(Organization)
admin.site.register(ArchivedOrganization)
admin.site.register(OrganizationSettings)
admin.site.register(Subscription)
