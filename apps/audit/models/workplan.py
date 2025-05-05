# apps/audit/models/workplan.py

import reversion
from datetime import date
from django.db import models
from django.urls import reverse
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from django_ckeditor_5.fields import CKEditor5Field
from django.contrib.contenttypes.fields import GenericRelation

from core.models.abstract_models import OrganizationOwnedModel, AuditableModel
from core.mixins.state import ApprovalStateMixin

@reversion.register()
class AuditWorkplan(ApprovalStateMixin, OrganizationOwnedModel, AuditableModel):
    """
    Audit workplan model with FSM-driven approval state, rich-text objectives,
    description, and tenant isolation.
    """
    code = models.CharField(
        max_length=8,
        db_index=True,
        verbose_name=_("Workplan Code"),
        help_text=_("Unique code for the audit workplan within the organization."),
    )
    name = models.CharField(
        max_length=512,
        db_index=True,
        verbose_name=_("Workplan Name"),
        help_text=_("Name of the audit workplan."),
    )
    fiscal_year = models.PositiveIntegerField(
        verbose_name=_("Fiscal Year"),
        help_text=_("Fiscal year to which the workplan applies."),
    )
    objectives = CKEditor5Field(
        'Objectives',
        config_name='extends',
        max_length=512,
        blank=True,
        null=True,
        help_text=_("Detailed Objectives of the audit workplan."),
    )    
    creation_date = models.DateField(
        auto_now_add=True,
        verbose_name=_("Creation Date"),
        help_text=_("Date when this workplan was created."),
    )
    description = CKEditor5Field(
        'Description',
        config_name='extends',
        max_length=512,
        blank=True,
        null=True,
        help_text=_("Detailed description of the audit workplan."),
    )

    approvals = GenericRelation(
        'audit.Approval',
        content_type_field='content_type',
        object_id_field='object_id',
        related_query_name='workplan',
        related_name='approvals',
    )

    class Meta:
        app_label = 'audit'
        verbose_name = _("Audit Workplan")
        verbose_name_plural = _("Audit Workplans")
        ordering = ['-creation_date', 'name']
        unique_together = (('organization', 'code'),)
        indexes = [
            models.Index(fields=['organization', 'code'], name='wp_org_code_idx'),
            models.Index(fields=['name'], name='wp_name_idx'),
        ]
        constraints = [
            models.CheckConstraint(
                check=models.Q(organization__isnull=False),
                name='organization_required_auditworkplan'
            )
        ]

    def __str__(self):
        return f"{self.name} ({self.code})"

    def get_absolute_url(self):
        return reverse('audit:workplan-detail', kwargs={'pk': self.pk})

    def clean(self):
        super().clean()

        # Fiscal year sanity
        current_year = date.today().year
        if self.fiscal_year < 2000 or self.fiscal_year > current_year + 1:
            raise ValidationError({'fiscal_year': _(
                'Fiscal year must be between 2000 and %(max_year)s'
            )}, params={'max_year': current_year + 1})

    def save(self, *args, **kwargs):
        # Skip full_clean() to avoid state validation issues
        with reversion.create_revision():
            if hasattr(self, 'last_modified_by') and self.last_modified_by:
                reversion.set_user(self.last_modified_by)
            # record the FSM field state
            reversion.set_comment(f"Saved workplan '{self.code}' (State: {self.state})")
            super().save(*args, **kwargs)

    def get_approvers(self):
        return self.organization.get_approvers()

    @property
    def engagements(self):
        return self.engagements.all()
