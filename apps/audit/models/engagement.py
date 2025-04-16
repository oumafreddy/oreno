# apps/audit/models/engagement.py

from django.db import models
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django.conf import settings
from django_ckeditor_5.fields import CKEditor5Field

from apps.core.models.abstract_models import OrganizationOwnedModel, AuditableModel
from apps.core.mixins.state import ApprovalStateMixin
from apps.audit.models.workplan import AuditWorkplan

class Engagement(ApprovalStateMixin, OrganizationOwnedModel, AuditableModel):
    """
    Model for audit engagements.

    Represents a specific engagement within an audit workplan.
    Includes audit details such as title, type, project dates, and textual descriptions.
    New fields (assigned_to and assigned_by) have been added so that engagements are
    assigned from the pool of registered users within an organization. Approval state
    is managed through the ApprovalStateMixin.
    """
    audit_workplan = models.ForeignKey(
        AuditWorkplan,
        on_delete=models.CASCADE,
        related_name='engagements',
        verbose_name=_("Audit Workplan"),
        help_text=_("The audit workplan to which this engagement belongs.")
    )
    title = models.CharField(
        max_length=255,
        verbose_name=_("Engagement Title"),
        help_text=_("Title of the engagement.")
    )
    engagement_type = models.CharField(
        max_length=80,
        blank=True,
        null=True,
        default='Compliance Audit',
        verbose_name=_("Engagement Type"),
        help_text=_("Type of audit engagement (e.g., Compliance Audit, Operational Audit).")
    )
    project_start_date = models.DateField(
        verbose_name=_("Project Start Date"),
        help_text=_("The start date of the engagement.")
    )
    target_end_date = models.DateField(
        blank=True,
        null=True,
        verbose_name=_("Target End Date"),
        help_text=_("Proposed end date for the engagement; leave blank if ongoing.")
    )
    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='engagements_assigned',
        verbose_name=_("Assigned To"),
        help_text=_("User assigned to this engagement from within the organization.")
    )
    assigned_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='engagements_assigned_by',
        verbose_name=_("Assigned By"),
        help_text=_("User who assigned this engagement.")
    )
    executive_summary = CKEditor5Field(
        'Executive Summary',
        config_name='extends',
        blank=True,
        null=True,
        help_text=_("Summary of the engagement.")
    )
    purpose = CKEditor5Field(
        'Purpose',
        config_name='extends',
        blank=True,
        null=True,
        help_text=_("Purpose of undertaking the engagement.")
    )
    background = CKEditor5Field(
        'Background',
        config_name='extends',
        blank=True,
        null=True,
        help_text=_("Background context relevant to the engagement.")
    )
    scope = CKEditor5Field(
        'Scope',
        config_name='extends',
        blank=True,
        null=True,
        help_text=_("Scope of audit procedures to be performed.")
    )
    project_objectives = CKEditor5Field(
        'Project Objectives',
        config_name='extends',
        blank=True,
        null=True,
        help_text=_("Specific objectives for the engagement.")
    )
    conclusion_description = CKEditor5Field(
        'Conclusion Description',
        config_name='extends',
        blank=True,
        null=True,
        help_text=_("Summary of conclusions drawn from the engagement.")
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
        help_text=_("Overall conclusion derived from the engagement.")
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
        help_text=_("Current status of the engagement.")
    )

    class Meta:
        verbose_name = _("Engagement")
        verbose_name_plural = _("Engagements")
        ordering = ['-project_start_date', 'title']
        indexes = [
            models.Index(fields=['organization']),
            models.Index(fields=['title']),
            models.Index(fields=['project_status']),
            models.Index(fields=['audit_workplan']),
        ]

    def __str__(self):
        return f"{self.title} ({self.audit_workplan.code})"

    def get_absolute_url(self):
        return reverse('audit:engagement_detail', kwargs={'pk': self.pk})

    def clean(self):
        """
        Validate that the project start date is before the target end date.
        """
        if self.project_start_date and self.target_end_date and self.project_start_date > self.target_end_date:
            from django.core.exceptions import ValidationError
            raise ValidationError(_('Target end date cannot be before the project start date.'))

    def get_approvers(self):
        """
        Retrieve the list of approvers for this engagement.
        This method delegates approval responsibility to the associated workplan.
        """
        return self.audit_workplan.get_approvers()
