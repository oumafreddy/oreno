# apps/audit/models/issue.py

import reversion
from django.db import models
from django.urls import reverse
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.conf import settings
from django_ckeditor_5.fields import CKEditor5Field

from core.models.abstract_models import OrganizationOwnedModel, AuditableModel
from audit.models.engagement import Engagement
from core.models.validators import validate_file_extension, validate_file_size

@reversion.register()
class Issue(OrganizationOwnedModel, AuditableModel):
    """
    Audit issue model with FSM approval, rich-text fields, file validators,
    and date checks.
    """
    code = models.CharField(
        max_length=16,
        db_index=True,
        verbose_name=_("Issue Code"),
    )
    issue_title = models.CharField(
        max_length=512,
        db_index=True,
        verbose_name=_("Issue Title"),
    )
    issue_description = CKEditor5Field(
        _('Issue Description'),
        config_name='extends',
        blank=True,
        null=True,
    )
    root_cause = CKEditor5Field(
        _('Root Cause'),
        config_name='extends',
        blank=True,
        null=True,
    )
    risks = CKEditor5Field(
        _('Risks'),
        config_name='extends',
        blank=True,
        null=True,
    )
    date_identified = models.DateField(
        verbose_name=_("Date Identified"),
    )
    issue_owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='issues_owned',
        verbose_name=_("Issue Owner"),
    )
    issue_owner_title = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name=_("Issue Owner Title"),
    )
    audit_procedures = CKEditor5Field(
        _('Audit Procedures'),
        config_name='extends',
        default='Bank reconciliation reperformance',
    )
    recommendation = CKEditor5Field(
        _('Recommendation'),
        config_name='extends',
        blank=True,
        null=True,
    )
    engagement = models.ForeignKey(
        Engagement,
        on_delete=models.CASCADE,
        related_name='issues',
        verbose_name=_("Engagement"),
    )

    SEVERITY_CHOICES = [
        ('high', _('High')),
        ('medium', _('Medium')),
        ('low', _('Low')),
    ]
    severity_status = models.CharField(
        max_length=12,
        choices=SEVERITY_CHOICES,
        default='high',
        db_index=True,
        verbose_name=_("Severity"),
    )

    ISSUE_STATUS_CHOICES = [
        ('open', _('Open')),
        ('in_progress', _('In Progress')),
        ('closed', _('Closed')),
    ]
    issue_status = models.CharField(
        max_length=56,
        choices=ISSUE_STATUS_CHOICES,
        default='open',
        db_index=True,
        verbose_name=_("Issue Status"),
    )

    REMEDIATION_CHOICES = [
        ('open', _('Open')),
        ('management_remediating', _('Management Remediating')),
        ('remediated_awaiting_verification', _('Remediated Awaiting Verification')),
        ('closed', _('Closed')),
    ]
    remediation_status = models.CharField(
        max_length=56,
        choices=REMEDIATION_CHOICES,
        default='open',
        db_index=True,
        verbose_name=_("Remediation Status"),
    )
    remediation_deadline_date = models.DateField(
        blank=True,
        null=True,
        verbose_name=_("Remediation Deadline"),
    )
    actual_remediation_date = models.DateField(
        blank=True,
        null=True,
        verbose_name=_("Actual Remediation Date"),
    )
    management_action_plan = CKEditor5Field(
        _('Management Action Plan'),
        config_name='extends',
        blank=True,
        null=True,
    )
    working_papers = models.FileField(
        upload_to='working_papers/',
        blank=True,
        null=True,
        validators=[validate_file_extension, validate_file_size],
        verbose_name=_("Working Papers"),
    )

    class Meta:
        app_label = 'audit'
        verbose_name = _('Issue')
        verbose_name_plural = _('Issues')
        ordering = ['-date_identified', 'issue_title']
        indexes = [
            models.Index(fields=['organization']),
            models.Index(fields=['code']),
            models.Index(fields=['issue_title']),
            models.Index(fields=['issue_status']),
            models.Index(fields=['severity_status']),
            models.Index(fields=['remediation_status']),
            models.Index(fields=['engagement']),
        ]

    def __str__(self):
        return f"{self.issue_title} ({self.issue_status})"

    def get_absolute_url(self):
        return reverse('audit:issue_detail', kwargs={'pk': self.pk})

    def clean(self):
        if self.date_identified > timezone.now().date():
            raise ValidationError(_('Date identified cannot be in the future.'))
        if self.remediation_deadline_date and self.actual_remediation_date and \
           self.actual_remediation_date < self.remediation_deadline_date:
            raise ValidationError(_('Actual remediation date cannot be before the deadline.'))
