# apps/audit/models/engagement.py

import reversion
from datetime import date
from django.db import models
from django.urls import reverse
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from django.conf import settings
from django_ckeditor_5.fields import CKEditor5Field
from django.contrib.contenttypes.fields import GenericRelation
from django.apps import apps
from simple_history.models import HistoricalRecords
from core.models.abstract_models import OrganizationOwnedModel, AuditableModel, SoftDeletionModel
from core.mixins.state import ApprovalStateMixin

@reversion.register()
class Engagement(ApprovalStateMixin, OrganizationOwnedModel, AuditableModel, SoftDeletionModel):
    """
    Audit engagement model with FSM state, rich-text fields, and assignments.
    """
    code = models.CharField(
        max_length=16,
        db_index=True,
        verbose_name=_("Engagement Code"),
        help_text=_("Unique code for identifying the engagement within a workplan."),
    )
    annual_workplan = models.ForeignKey(
        'audit.AuditWorkplan',
        on_delete=models.CASCADE,
        related_name='engagements',
        verbose_name=_('Annual Workplan'),
        help_text=_('The annual workplan this engagement belongs to'),
    )
    title = models.CharField(
        max_length=255,
        verbose_name=_("Engagement Title"),
        help_text=_('Title of the audit engagement'),
    )
    criteria = CKEditor5Field(
        _('Audit Criteria'),
        config_name='extends',
        blank=True,
        null=True,
        help_text=_('Standards, regulations, or policies that form the basis for evaluation'),
    )
    estimated_hours = models.PositiveIntegerField(
        default=0,
        verbose_name=_('Estimated Hours'),
        help_text=_('Estimated audit hours for this engagement'),
    )
    engagement_type = models.CharField(
        max_length=80,
        blank=True,
        null=True,
        default='Compliance Audit',
        verbose_name=_("Engagement Type"),
    )
    project_start_date = models.DateField(
        verbose_name=_("Project Start Date"),
        help_text=_('Actual start date of the audit engagement'),
    )
    target_end_date = models.DateField(
        blank=True,
        null=True,
        verbose_name=_("Target End Date"),
    )
    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='engagements_assigned',
        verbose_name=_("Assigned To"),
    )
    assigned_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='engagements_created',
        verbose_name=_("Assigned By"),
    )
    executive_summary = CKEditor5Field(
        _('Executive Summary'),
        config_name='extends',
        blank=True,
        null=True,
    )
    purpose = CKEditor5Field(
        _('Purpose'),
        config_name='extends',
        blank=True,
        null=True,
    )
    background = CKEditor5Field(
        _('Background'),
        config_name='extends',
        blank=True,
        null=True,
    )
    scope = CKEditor5Field(
        _('Scope'),
        config_name='extends',
        blank=True,
        null=True,
    )
    conclusion_description = CKEditor5Field(
        _('Conclusion Description'),
        config_name='extends',
        blank=True,
        null=True,
    )
    CONCLUSION_CHOICES = [
        ('satisfactory', _('Satisfactory')),
        ('needs_improvement', _('Needs Improvement')),
        ('unsatisfactory', _('Unsatisfactory')),
        ('significant_improvement_needed', _('Significant Improvement Needed')),
        ('not_rated', _('Not Rated')),
    ]
    conclusion = models.CharField(
        max_length=32,
        choices=CONCLUSION_CHOICES,
        default='satisfactory',
        verbose_name=_("Conclusion"),
    )
    PROJECT_STATUS_CHOICES = [
        ('planning', _('Planning')),
        ('fieldwork', _('Fieldwork')),
        ('reporting', _('Reporting')),
        ('review', _('Review')),
        ('completed', _('Completed')),
        ('cancelled', _('Cancelled')),
    ]
    project_status = models.CharField(
        max_length=32,
        choices=PROJECT_STATUS_CHOICES,
        default='planning',
        db_index=True,
        verbose_name=_("Project Status"),
        help_text=_('Current status of the audit engagement'),
    )
    
    # GIAS 2024 compliance fields
    field_work_start_date = models.DateField(
        blank=True,
        null=True,
        verbose_name=_('Fieldwork Start Date'),
        help_text=_('Date when fieldwork began'),
    )
    field_work_end_date = models.DateField(
        blank=True,
        null=True,
        verbose_name=_('Fieldwork End Date'),
        help_text=_('Date when fieldwork was completed'),
    )
    report_issued_date = models.DateField(
        blank=True,
        null=True,
        verbose_name=_('Report Issued Date'),
        help_text=_('Date when final report was issued'),
    )
    APPROVAL_STATUS_CHOICES = [
        ('draft', _('Draft')),
        ('submitted', _('Submitted for Review')),
        ('reviewed', _('Reviewed')),
        ('approved', _('Approved')),
        ('rejected', _('Rejected')),
    ]
    approval_status = models.CharField(
        max_length=20,
        choices=APPROVAL_STATUS_CHOICES,
        default='draft',
        verbose_name=_('Approval Status'),
        help_text=_('Current approval status of the engagement'),
    )
    approved_date = models.DateField(
        null=True,
        blank=True,
        verbose_name=_('Approved Date'),
        help_text=_('Date when this engagement was approved'),
    )
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='approved_engagements',
        verbose_name=_('Approved By'),
    )
    approvals = GenericRelation(
        'audit.Approval',
        content_type_field='content_type',
        object_id_field='object_id',
        related_query_name='engagement',
        related_name='approvals',
    )
    history = HistoricalRecords()

    class Meta:
        app_label = 'audit'
        verbose_name = _('Engagement')
        verbose_name_plural = _('Engagements')
        ordering = ['-project_start_date', 'code']
        constraints = [
            models.UniqueConstraint(
                fields=['organization', 'annual_workplan', 'code'],
                name='unique_engagement_per_workplan'
            ),
            models.CheckConstraint(
                check=models.Q(organization__isnull=False),
                name='organization_required_engagement'
            )
        ]
        indexes = [
            models.Index(fields=['organization']),
            models.Index(fields=['annual_workplan']),
            models.Index(fields=['code']),
            models.Index(fields=['project_status']),
            models.Index(fields=['approval_status']),
        ]

    def clean(self):
        if self.target_end_date and self.project_start_date > self.target_end_date:
            raise ValidationError(
                _('Project start date must be on or before target end date.')
            )

    def save(self, *args, **kwargs):
        # Skip full_clean() to avoid state validation issues
        with reversion.create_revision():
            if hasattr(self, 'last_modified_by') and self.last_modified_by:
                reversion.set_user(self.last_modified_by)
            # record the FSM field state
            reversion.set_comment(f"Saved engagement '{self.code}' (State: {self.state}, Approval: {self.approval_status})")
            
            # Update approval fields if status changes to approved
            if self.approval_status == 'approved' and not self.approved_date:
                self.approved_date = date.today()
                if hasattr(self, 'last_modified_by') and self.last_modified_by:
                    self.approved_by = self.last_modified_by
                    
            # Update project status based on dates
            if self.field_work_start_date and not self.field_work_end_date and self.project_status == 'planning':
                self.project_status = 'fieldwork'
            elif self.field_work_end_date and not self.report_issued_date and self.project_status == 'fieldwork':
                self.project_status = 'reporting'
            elif self.report_issued_date and self.project_status == 'reporting':
                self.project_status = 'review'
                
            super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('audit:engagement-detail', kwargs={'pk': self.pk})

    def get_approvers(self):
        return self.annual_workplan.get_approvers()

    def __str__(self):
        return f"{self.title} ({self.code})"

    @property
    def all_issues(self):
        """
        Returns all issues linked to this engagement via objectives > procedures > procedure_results.
        """
        Issue = apps.get_model('audit', 'Issue')
        return Issue.objects.filter(
            procedure__risk__objective__engagement=self
        )

    @property
    def all_procedures(self):
        """
        Returns all procedures linked to this engagement via objectives.
        """
        Procedure = apps.get_model('audit', 'Procedure')
        return Procedure.objects.filter(risk__objective__engagement=self)

    @property
    def all_risks(self):
        """
        Returns all risks linked to this engagement via objectives.
        """
        Risk = apps.get_model('audit', 'Risk')
        return Risk.objects.filter(objective__engagement=self)

    @property
    def all_followups(self):
        """
        Returns all follow-up actions linked to this engagement via issues > recommendations > followup_actions.
        """
        FollowUpAction = apps.get_model('audit', 'FollowUpAction')
        return FollowUpAction.objects.filter(issue__procedure__risk__objective__engagement=self)

    @property
    def all_retests(self):
        """
        Returns all retests linked to this engagement via issues > recommendations > retests.
        """
        IssueRetest = apps.get_model('audit', 'IssueRetest')
        return IssueRetest.objects.filter(issue__procedure__risk__objective__engagement=self)

    @property
    def all_notes(self):
        """
        Returns all notes linked to this engagement, its issues, or its procedures (via generic relation).
        """
        Note = apps.get_model('audit', 'Note')
        from django.contrib.contenttypes.models import ContentType
        engagement_ct = ContentType.objects.get_for_model(self)
        issue_ct = ContentType.objects.get(app_label='audit', model='issue')
        procedure_ct = ContentType.objects.get(app_label='audit', model='procedure')
        # All issues and procedures for this engagement
        issue_ids = self.all_issues.values_list('id', flat=True)
        procedure_ids = self.all_procedures.values_list('id', flat=True)
        return Note.objects.filter(
            (
                models.Q(content_type=engagement_ct, object_id=self.pk) |
                models.Q(content_type=issue_ct, object_id__in=issue_ids) |
                models.Q(content_type=procedure_ct, object_id__in=procedure_ids)
            )
        )
