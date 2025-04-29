from django.db import models
from django_tenants.models import TenantMixin
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django_ckeditor_5.fields import CKEditor5Field
from django.contrib.auth import get_user_model
from django.core.validators import RegexValidator

from core.models.abstract_models import AuditableModel  # Inherits TimeStampedModel
from apps.core.mixins import AuditMixin, OrganizationMixin
from .settings import OrganizationSettings


class Organization(TenantMixin, AuditMixin, models.Model):
    """
    Organization (Tenant) in the system.
    Inherits TenantMixin to work with django-tenants.
    """

    # django-tenants required field:
    schema_name = models.SlugField(
        max_length=63,
        unique=True,
        help_text=_("Postgres schema name for this tenant"),
    )

    # Business-specific fields:
    name = models.CharField(
        max_length=255,
        unique=True,
        default='Default Organization',
        help_text=_('The name of the organization')
    )
    slug = models.SlugField(
        max_length=255,
        unique=True,
        blank=True,
        help_text=_('URL-friendly version of the organization name')
    )
    code = models.CharField(
        max_length=20,
        unique=True,
        default='ORG001',
        help_text=_('Unique identifier code for the organization'),
        validators=[RegexValidator(r'^[A-Z0-9]+$', 'Only uppercase letters and numbers allowed')]
    )
    description = models.TextField(blank=True)    
    logo = models.ImageField(upload_to='organizations/logos/', null=True, blank=True)
    website = models.URLField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _('Organization')
        verbose_name_plural = _('Organizations')
        ordering = ['name']

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        # Auto-generate slug if missing
        if not self.slug:
            self.slug = self.name.lower().replace(' ', '-')
        super().save(*args, **kwargs)
        # Ensure a settings object exists for this organization
        OrganizationSettings.objects.get_or_create(organization=self)

    def get_members(self):
        return get_user_model().objects.filter(organization=self)

    def get_admins(self):
        return self.get_members().filter(role='admin')

    def get_departments(self):
        from .department import Department
        return Department.objects.filter(organization=self)

    def get_subscription_status(self):
        try:
            return self.settings.subscription_status
        except OrganizationSettings.DoesNotExist:
            return 'inactive'

    @property
    def settings(self):
        return OrganizationSettings.objects.get_or_create(organization=self)[0]

    def get_absolute_url(self):
        return reverse('organizations:organization_detail', args=[str(self.id)])
