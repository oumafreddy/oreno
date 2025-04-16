# apps/audit/models/workplan.py

from django.db import models
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django_ckeditor_5.fields import CKEditor5Field

from apps.core.models.abstract_models import OrganizationOwnedModel, AuditableModel
from apps.core.mixins.state import ApprovalStateMixin

class AuditWorkplan(ApprovalStateMixin, OrganizationOwnedModel, AuditableModel):
    """
    Model for audit workplans.

    This model encapsulates audit workplan details, including a unique code,
    descriptive name, fiscal year, set of objectives (stored in JSON format),
    a creation date, and an optional detailed description. It includes approval state
    transitions via ApprovalStateMixin.
    """
    code = models.CharField(
        max_length=8,
        db_index=True,
        verbose_name=_("Workplan Code"),
        help_text=_("Unique code for the audit workplan.")
    )
    name = models.CharField(
        max_length=512,
        db_index=True,
        verbose_name=_("Workplan Name"),
        help_text=_("Name of the audit workplan.")
    )
    fiscal_year = models.PositiveIntegerField(
        verbose_name=_("Fiscal Year"),
        help_text=_("Fiscal year to which the workplan applies.")
    )
    objectives = models.JSONField(
        verbose_name=_("Objectives"),
        help_text=_("Audit objectives specified in structured (JSON) format.")
    )
    creation_date = models.DateField(
        auto_now_add=True,
        verbose_name=_("Creation Date")
    )
    description = CKEditor5Field(
        'Description',
        config_name='extends',
        max_length=512,
        blank=True,
        null=True,
        help_text=_("Detailed description of the audit workplan.")
    )

    class Meta:
        verbose_name = _("Audit Workplan")
        verbose_name_plural = _("Audit Workplans")
        ordering = ['-creation_date', 'name']
        indexes = [
            models.Index(fields=['organization', 'code']),
            models.Index(fields=['name']),
        ]

    def __str__(self):
        return f"{self.name} ({self.code})"

    def get_absolute_url(self):
        return reverse('audit:workplan_detail', kwargs={'pk': self.pk})

    def get_approvers(self):
        """
        Returns a list of users who should approve this workplan.
        Assumes the related Organization model has a method get_supervisors().
        """
        if hasattr(self.organization, 'get_supervisors'):
            return self.organization.get_supervisors()
        return []
