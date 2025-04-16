# apps/organizations/models/organization.py

from django.db import models
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django_ckeditor_5.fields import CKEditor5Field

from apps.core.models.abstract_models import AuditableModel  # Inherits TimeStampedModel

class Organization(AuditableModel):
    """
    Represents a subscribing customer or tenant in the system.
    Supports multi-tenancy via unique customer_code.
    """

    customer_code = models.CharField(
        max_length=8,
        unique=True,
        db_index=True,
        verbose_name=_("Customer Code"),
        help_text=_("Unique 8-character code to identify this organization.")
    )
    customer_name = models.CharField(
        max_length=512,
        db_index=True,
        verbose_name=_("Customer Name"),
        help_text=_("The official name of the organization.")
    )
    financial_year_end_date = models.DateField(
        verbose_name=_("Financial Year End Date"),
        help_text=_("Closing date of the organization’s fiscal year.")
    )
    logo = models.ImageField(
        upload_to='organization_logos/',
        null=True,
        blank=True,
        verbose_name=_("Organization Logo"),
        help_text=_("Optional logo for branding within the system.")
    )
    customer_industry = models.CharField(
        max_length=32,
        blank=True,
        null=True,
        db_index=True,
        verbose_name=_("Industry"),
        help_text=_("Optional industry classification for reporting.")
    )

    class Meta:
        verbose_name = _("Organization")
        verbose_name_plural = _("Organizations")
        ordering = ['customer_name']
        indexes = [
            models.Index(fields=['customer_code']),
            models.Index(fields=['customer_name']),
            models.Index(fields=['customer_industry']),
        ]

    def __str__(self):
        return f"{self.customer_name} ({self.customer_industry or 'N/A'})"

    def get_absolute_url(self):
        """
        Returns the canonical URL for this organization (used in templates).
        """
        return reverse('organizations:organization_detail', args=[str(self.id)])

    def get_employees(self):
        """
        Returns all users associated with this organization.
        Assumes a related_name='users' in CustomUser model.
        """
        return self.users.all().select_related('profile')
