# apps/audit/models/issue.py

from django.db import models
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.conf import settings
from django_ckeditor_5.fields import CKEditor5Field

from apps.core.models.abstract_models import OrganizationOwnedModel, AuditableModel
from apps.audit.models.engagement import Engagement
from apps.core.models.validators import validate_file_extension, validate_file_size


class Issue(OrganizationOwnedModel, AuditableModel):
    """
    Model for audit issues.

    In version 2, improvements include:
      - Using a ForeignKey for the issue owner (linked to the custom user model)
      - Enhancing validations on dates
      - Standardized rich-text fields with CKEditor5 for long text entries
      - Linking the issue to an engagement
      - Using custom validators for uploaded working papers
    """

    code = models.CharField(
        max_length=16,
        db_index=True,
        verbose_name=_("Issue Code"),
        help_text=_("Unique code for identifying the issue.")
    )
    issue_title = models.CharField(
        max_length=512,
        db_index=True,
        verbose_name=_("Issue Title"),
        help_text=_("Title of the issue.")
    )
    issue_description = CKEditor5Field(
        'Issue Description',
        config_name='extends',
        blank=True,
        null=True,
        help_text=_("Detailed description of the issue.")
    )
    root_cause = CKEditor5Field(
        'Root Cause',
        config_name='extends',
        blank=True,
        null=True,
        help_text=_("Analyzed root cause of the issue.")
    )
    risks = CKEditor5Field(
        'Risks',
        config_name='extends',
        blank=True,
        null=True,
        help_text=_("Risks associated with the issue.")
    )
    date_identified = models.DateField(
        verbose_name=_("Date Identified"),
        help_text=_("The date the issue was identified.")
    )
    # Improved: Instead of a plain CharField, we reference the custom user model.
    issue_owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='issues_owned',
        verbose_name=_("Issue Owner"),
        help_text=_("User responsible for the issue.")
    )
    issue_owner_title = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name=_("Issue Owner Title"),
        help_text=_("Title or designation of the issue owner.")
    )
    audit_procedures = CKEditor5Field(
        'Audit Procedures',
        config_name='extends',
        default='Bank reconciliation reperformance',
        verbose_name=_("Audit Procedures"),
        help_text=_("The procedures followed during the audit.")
    )
    recommendation = CKEditor5Field(
        'Recommendation',
        config_name='extends',
        blank=True,
        null=True,
        verbose_name=_("Recommendation"),
        help_text=_("Recommended corrective actions.")
    )
    # Link Issue to Engagement
    engagement = models.ForeignKey(
        Engagement,
        on_delete=models.CASCADE,
        related_name='issues',
        verbose_name=_("Engagement"),
        help_text=_("The engagement to which this issue belongs.")
    )

    # Severity Choices
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
        help_text=_("Severity of the issue.")
    )

    # Issue Status Choices
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
        help_text=_("Current status of the issue.")
    )

    # Remediation Status Choices
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
        help_text=_("Status of remediation measures.")
    )
    remediation_deadline_date = models.DateField(
        blank=True,
        null=True,
        verbose_name=_("Remediation Deadline"),
        help_text=_("Deadline for remediation actions.")
    )
    actual_remediation_date = models.DateField(
        blank=True,
        null=True,
        verbose_name=_("Actual Remediation Date"),
        help_text=_("The actual date when remediation was completed.")
    )
    management_action_plan = CKEditor5Field(
        'Management Action Plan',
        config_name='extends',
        blank=True,
        null=True,
        verbose_name=_("Management Action Plan"),
        help_text=_("Action plan provided by management to address the issue.")
    )
    working_papers = models.FileField(
        upload_to='working_papers/',
        blank=True,
        null=True,
        validators=[validate_file_extension, validate_file_size],
        verbose_name=_("Working Papers"),
        help_text=_("Supporting documents for this issue.")
    )

    class Meta:
        verbose_name = _("Issue")
        verbose_name_plural = _("Issues")
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
        """
        Return the URL to access the issue instance.
        """
        return reverse('audit:issue_detail', kwargs={'pk': self.pk})

    def clean(self):
        """
        Validate the issue data:
          - Date identified cannot be in the future.
          - If both remediation_deadline_date and actual_remediation_date are provided,
            ensure the actual remediation date is not before the deadline.
        """
        if self.date_identified and self.date_identified > timezone.now().date():
            raise ValidationError(_('Date identified cannot be in the future.'))
        
        if (self.remediation_deadline_date and self.actual_remediation_date and 
                self.remediation_deadline_date > self.actual_remediation_date):
            raise ValidationError(_('Actual remediation date cannot be before the remediation deadline.'))
