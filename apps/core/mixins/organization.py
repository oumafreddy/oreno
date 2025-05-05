# apps/core/mixins/organization.py
from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError

class OrganizationMixin(models.Model):
    """
    A mixin that adds organization-related fields and methods to a model.
    """
    organization = models.ForeignKey(
        'users.Organization',
        on_delete=models.CASCADE,
        related_name='%(class)ss',
        help_text='The organization this record belongs to'
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='%(class)s_created',
        help_text='The user who created this record'
    )
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='%(class)s_updated',
        help_text='The user who last updated this record'
    )

    class Meta:
        abstract = True

    def clean(self):
        """
        Ensure the creating/updating user belongs to the organization
        """
        if self.created_by and not self.created_by.organization == self.organization:
            raise ValidationError({
                'created_by': 'User must belong to the same organization'
            })
        if self.updated_by and not self.updated_by.organization == self.organization:
            raise ValidationError({
                'updated_by': 'User must belong to the same organization'
            })

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    @property
    def org_name(self):
        """Return the organization name"""
        return self.organization.name if self.organization else None

class OrganizationScopedQuerysetMixin:
    """
    DRF mixin to enforce multi-tenant queryset filtering by request.tenant (or request.organization).
    Inherit this in all ModelViewSets and DRF generic views that expose org-owned data.
    """
    def get_queryset(self):
        base_qs = super().get_queryset()
        org = getattr(self.request, 'tenant', None) or getattr(self.request, 'organization', None)
        if org is not None and hasattr(base_qs.model, 'organization'):
            return base_qs.filter(organization=org)
        return base_qs 