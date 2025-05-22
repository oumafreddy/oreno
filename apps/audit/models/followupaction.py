from django.db import models
from django.utils.translation import gettext_lazy as _
from django.conf import settings
from core.models.abstract_models import OrganizationOwnedModel, AuditableModel, SoftDeletionModel
from .recommendation import Recommendation
from django_ckeditor_5.fields import CKEditor5Field
from simple_history.models import HistoricalRecords
from .issue import Issue

class FollowUpAction(OrganizationOwnedModel, AuditableModel, SoftDeletionModel):
    STATUS_CHOICES = [
        ('open', _('Open')),
        ('in_progress', _('In Progress')),
        ('completed', _('Completed')),
        ('overdue', _('Overdue')),
    ]
    issue = models.ForeignKey(
        Issue,
        on_delete=models.CASCADE,
        related_name='followup_actions',
        verbose_name=_('Issue'),
        null=True,
        blank=True,
    )
    description = CKEditor5Field(_('Action Description'), config_name='extends', blank=True, null=True)
    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='followup_actions_assigned',
        verbose_name=_('Assigned To'),
    )
    due_date = models.DateField(blank=True, null=True, verbose_name=_('Due Date'))
    status = models.CharField(max_length=16, choices=STATUS_CHOICES, default='open', verbose_name=_('Status'))
    completed_at = models.DateTimeField(blank=True, null=True, verbose_name=_('Completed At'))
    notes = CKEditor5Field(_('Notes'), config_name='extends', blank=True, null=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='followup_actions_created',
        verbose_name=_('Created By'),
    )
    created_at = models.DateTimeField(auto_now_add=True)
    history = HistoricalRecords()

    class Meta:
        app_label = 'audit'
        verbose_name = _('Follow-Up Action')
        verbose_name_plural = _('Follow-Up Actions')
        ordering = ['-created_at']

    def __str__(self):
        issue_ref = f"{self.issue}" if self.issue else "No Issue"
        desc = (self.description[:40] + '...') if self.description else 'No description'
        return f"{issue_ref} - {desc} ({self.get_status_display()})"