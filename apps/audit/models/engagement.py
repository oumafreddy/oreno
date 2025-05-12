# apps/audit/models/engagement.py

import reversion
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
from .workplan import AuditWorkplan

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
    audit_workplan = models.ForeignKey(
        AuditWorkplan,
        on_delete=models.CASCADE,
        related_name='engagements',
        verbose_name=_("Audit Workplan"),
    )
    title = models.CharField(
        max_length=255,
        verbose_name=_("Engagement Title"),
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
    ]
    conclusion = models.CharField(
        max_length=32,
        choices=CONCLUSION_CHOICES,
        default='satisfactory',
        verbose_name=_("Conclusion"),
    )
    PROJECT_STATUS_CHOICES = [
        ('draft', _('Draft')),
        ('active', _('Active')),
        ('closed', _('Closed')),
    ]
    project_status = models.CharField(
        max_length=32,
        choices=PROJECT_STATUS_CHOICES,
        default='draft',
        db_index=True,
        verbose_name=_("Project Status"),
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
                fields=['organization', 'audit_workplan', 'code'],
                name='unique_engagement_per_workplan'
            ),
            models.CheckConstraint(
                check=models.Q(organization__isnull=False),
                name='organization_required_engagement'
            )
        ]
        indexes = [
            models.Index(fields=['organization']),
            models.Index(fields=['audit_workplan']),
            models.Index(fields=['code']),
            models.Index(fields=['project_status']),
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
            reversion.set_comment(f"Saved engagement '{self.code}' (State: {self.state})")
            super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('audit:engagement-detail', kwargs={'pk': self.pk})

    def get_approvers(self):
        return self.audit_workplan.get_approvers()

    def __str__(self):
        return f"{self.title} ({self.code})"

    @property
    def all_issues(self):
        """
        Returns all issues linked to this engagement via objectives > procedures > procedure_results.
        """
        Issue = apps.get_model('audit', 'Issue')
        return Issue.objects.filter(
            procedure_result__procedure__objective__engagement=self
        )

    @property
    def all_procedures(self):
        """
        Returns all procedures linked to this engagement via objectives.
        """
        Procedure = apps.get_model('audit', 'Procedure')
        return Procedure.objects.filter(objective__engagement=self)

    @property
    def all_followups(self):
        """
        Returns all follow-up actions linked to this engagement via issues > recommendations > followup_actions.
        """
        FollowUpAction = apps.get_model('audit', 'FollowUpAction')
        return FollowUpAction.objects.filter(recommendation__issue__procedure_result__procedure__objective__engagement=self)

    @property
    def all_retests(self):
        """
        Returns all retests linked to this engagement via issues > recommendations > retests.
        """
        IssueRetest = apps.get_model('audit', 'IssueRetest')
        return IssueRetest.objects.filter(recommendation__issue__procedure_result__procedure__objective__engagement=self)

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
