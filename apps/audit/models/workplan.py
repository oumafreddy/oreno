# apps/audit/models/workplan.py
# Updated for GIAS 2024 compliance

import reversion
from datetime import date
from django.db import models
from django.urls import reverse
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from django.conf import settings
from django_ckeditor_5.fields import CKEditor5Field
from django.contrib.contenttypes.fields import GenericRelation
from simple_history.models import HistoricalRecords

from core.models.abstract_models import OrganizationOwnedModel, AuditableModel, SoftDeletionModel
from core.mixins.state import ApprovalStateMixin

@reversion.register()
class AuditWorkplan(ApprovalStateMixin, OrganizationOwnedModel, AuditableModel, SoftDeletionModel):
    """
    Annual Audit Workplan model with FSM-driven approval state, rich-text objectives,
    description, and tenant isolation. Enhanced for GIAS 2024 compliance.
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
        verbose_name=_('Fiscal Year'),
        help_text=_('Fiscal year to which the workplan applies.'),
    )
    estimated_total_hours = models.PositiveIntegerField(
        default=0,
        verbose_name=_('Estimated Total Hours'),
        help_text=_('Estimated total audit hours for the entire workplan.'),
    )
    priority_ranking = models.PositiveSmallIntegerField(
        default=1,
        verbose_name=_('Priority Ranking'),
        help_text=_('Priority ranking of this workplan (1 = highest)'),
    )
    APPROVAL_STATUS_CHOICES = [
        ('draft', _('Draft')),
        ('submitted', _('Submitted')),
        ('approved', _('Approved')),
        ('rejected', _('Rejected')),
    ]
    approval_status = models.CharField(
        max_length=20,
        choices=APPROVAL_STATUS_CHOICES,
        default='draft',
        verbose_name=_('Approval Status'),
        help_text=_('Current approval status of the workplan'),
    )
    approved_date = models.DateField(
        null=True,
        blank=True,
        verbose_name=_('Approved Date'),
        help_text=_('Date when this workplan was approved.'),
    )
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='approved_workplans',
        verbose_name=_('Approved By'),
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

    history = HistoricalRecords()

    class Meta:
        app_label = 'audit'
        verbose_name = _("Annual Workplan")
        verbose_name_plural = _("Annual Workplans")
        ordering = ['-creation_date', 'name']
        unique_together = (('organization', 'code'),)
        indexes = [
            models.Index(fields=['organization', 'code'], name='wp_org_code_idx'),
            models.Index(fields=['name'], name='wp_name_idx'),
            models.Index(fields=['fiscal_year'], name='wp_fiscal_year_idx'),
            models.Index(fields=['approval_status'], name='wp_approval_status_idx'),
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
            reversion.set_comment(f"Saved workplan '{self.code}' (Approval Status: {self.approval_status})")
            
            # Update approval fields if status changes to approved
            if self.approval_status == 'approved' and not self.approved_date:
                self.approved_date = date.today()
                if hasattr(self, 'last_modified_by') and self.last_modified_by:
                    self.approved_by = self.last_modified_by
                    
            super().save(*args, **kwargs)

    def get_approvers(self):
        return self.organization.get_approvers()

    @property
    def engagements(self):
        """
        Returns all engagements linked to this workplan.
        Uses a lazy relationship to avoid circular imports.
        """
        Engagement = self._meta.apps.get_model('audit', 'Engagement')
        return Engagement.objects.filter(annual_workplan=self)

    @property
    def all_procedures(self):
        """
        Returns all procedures linked to this workplan via engagements > objectives > risks > procedures.
        """
        Procedure = self._meta.apps.get_model('audit', 'Procedure')
        return Procedure.objects.filter(risk__objective__engagement__annual_workplan=self)

    @property
    def all_issues(self):
        """
        Returns all issues linked to this workplan via engagements > objectives > risks > procedures > issues.
        """
        Issue = self._meta.apps.get_model('audit', 'Issue')
        return Issue.objects.filter(procedure__risk__objective__engagement__annual_workplan=self)

    @property
    def all_notes(self):
        """
        Returns all notes linked to this workplan, its engagements, objectives, procedures, or issues (via generic relation).
        """
        Note = self._meta.apps.get_model('audit', 'Note')
        from django.contrib.contenttypes.models import ContentType
        workplan_ct = ContentType.objects.get_for_model(self)
        engagement_ct = ContentType.objects.get(app_label='audit', model='engagement')
        objective_ct = ContentType.objects.get(app_label='audit', model='objective')
        procedure_ct = ContentType.objects.get(app_label='audit', model='procedure')
        issue_ct = ContentType.objects.get(app_label='audit', model='issue')
        # All related IDs
        engagement_ids = self.engagements.values_list('id', flat=True)
        objective_ids = self.engagements.values_list('objectives__id', flat=True)
        procedure_ids = self.all_procedures.values_list('id', flat=True)
        issue_ids = self.all_issues.values_list('id', flat=True)
        return Note.objects.filter(
            (
                models.Q(content_type=workplan_ct, object_id=self.pk) |
                models.Q(content_type=engagement_ct, object_id__in=engagement_ids) |
                models.Q(content_type=objective_ct, object_id__in=objective_ids) |
                models.Q(content_type=procedure_ct, object_id__in=procedure_ids) |
                models.Q(content_type=issue_ct, object_id__in=issue_ids)
            )
        )
