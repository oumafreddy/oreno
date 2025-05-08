# apps/audit/models/engagement.py

import reversion
from django.db import models
from django.urls import reverse
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from django.conf import settings
from django_ckeditor_5.fields import CKEditor5Field
from django.contrib.contenttypes.fields import GenericRelation

from core.models.abstract_models import OrganizationOwnedModel, AuditableModel
from core.mixins.state import ApprovalStateMixin
from .workplan import AuditWorkplan

@reversion.register()
class Engagement(ApprovalStateMixin, OrganizationOwnedModel, AuditableModel):
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
    project_objectives = CKEditor5Field(
        _('Project Objectives'),
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
