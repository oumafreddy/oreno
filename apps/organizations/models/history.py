# apps/organizations/models/history.py

from django.db import models
from django.conf import settings
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from core.models.abstract_models import AuditableModel  # Already includes TimeStampedModel
from django_ckeditor_5.fields import CKEditor5Field

class ArchivedOrganization(AuditableModel):
    """
    Represents an archived (historical) organization entry.

    This model captures key metadata when an organization is deactivated or unsubscribed,
    allowing auditability without affecting the active tenant records.
    """
    original_org_id = models.IntegerField(
        verbose_name=_("Original Organization ID"),
        help_text=_("ID of the organization as it existed before archival.")
    )
    customer_code = models.CharField(
        max_length=8,
        db_index=True,
        verbose_name=_("Customer Code")
    )
    customer_name = models.CharField(
        max_length=512,
        db_index=True,
        verbose_name=_("Customer Name")
    )
    archived_reason = models.TextField(
        verbose_name=_("Reason for Archiving"),
        blank=True,
        help_text=_("Reason this organization was archived or unsubscribed.")
    )
    archived_by_user = models.ForeignKey(
        'users.CustomUser',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='archived_organizations',
        verbose_name=_("Archived By")
    )
    financial_year_end_date = models.DateField(
        verbose_name=_("Financial Year End Date"),
        null=True,
        blank=True
    )
    customer_industry = models.CharField(
        max_length=64,
        null=True,
        blank=True,
        db_index=True,
        verbose_name=_("Industry")
    )
    logo_path = models.CharField(
        max_length=512,
        null=True,
        blank=True,
        verbose_name=_("Archived Logo Path"),
        help_text=_("Path to the archived logo file (if retained).")
    )
    was_active = models.BooleanField(
        default=True,
        verbose_name=_("Was Active"),
        help_text=_("Whether the organization was active at time of archival.")
    )

    class Meta:
        verbose_name = _("Archived Organization")
        verbose_name_plural = _("Archived Organizations")
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['customer_code']),
            models.Index(fields=['customer_name']),
            models.Index(fields=['archived_by_user']),
        ]
        constraints = [
            models.CheckConstraint(
                check=models.Q(original_org_id__isnull=False),
                name='organization_required_archivedorganization'
            )
        ]

    def __str__(self):
        return f"{self.customer_name} [ARCHIVED]"

    def get_absolute_url(self):
        """
        Optionally returns a URL where the archived organization detail can be viewed.
        """
        return reverse('archived_organization_detail', args=[str(self.id)])

    def restore_context(self):
        """
        Returns a dict that could be used to recreate an Organization instance if needed.
        """
        return {
            'customer_code': self.customer_code,
            'customer_name': self.customer_name,
            'financial_year_end_date': self.financial_year_end_date,
            'customer_industry': self.customer_industry,
        }
