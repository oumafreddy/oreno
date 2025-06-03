import reversion
from datetime import date, datetime
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.conf import settings
from django.contrib.contenttypes.fields import GenericRelation
from core.models.abstract_models import OrganizationOwnedModel, AuditableModel, SoftDeletionModel
from .recommendation import Recommendation
from django_ckeditor_5.fields import CKEditor5Field
from simple_history.models import HistoricalRecords
from .issue import Issue

@reversion.register()
class FollowUpAction(OrganizationOwnedModel, AuditableModel, SoftDeletionModel):
    """Follow-up action model for GIAS 2024 compliance.
    Used to track actions taken to address issues and implement recommendations.
    """
    STATUS_CHOICES = [
        ('not_started', _('Not Started')),
        ('in_progress', _('In Progress')),
        ('completed', _('Completed')),
        ('overdue', _('Overdue')),
        ('deferred', _('Deferred')),
        ('cancelled', _('Cancelled')),
    ]
    
    PRIORITY_CHOICES = [
        ('low', _('Low')),
        ('medium', _('Medium')),
        ('high', _('High')),
        ('critical', _('Critical')),
    ]
    issue = models.ForeignKey(
        Issue,
        on_delete=models.CASCADE,
        related_name='followup_actions',
        verbose_name=_('Issue'),
        null=True,
        blank=True,
        help_text=_('Associated issue for this follow-up action')
    )
    
    recommendation = models.ForeignKey(
        Recommendation,
        on_delete=models.CASCADE,
        related_name='followup_actions',
        verbose_name=_('Recommendation'),
        null=True,
        blank=True,
        help_text=_('Associated recommendation for this follow-up action')
    )
    title = models.CharField(
        max_length=255, 
        verbose_name=_('Action Title'),
        help_text=_('Brief title of the follow-up action')
    )
    
    description = CKEditor5Field(
        _('Action Description'), 
        config_name='extends', 
        blank=True, 
        null=True,
        help_text=_('Detailed description of the follow-up action')
    )
    
    priority = models.CharField(
        max_length=10,
        choices=PRIORITY_CHOICES,
        default='medium',
        verbose_name=_('Priority'),
        help_text=_('Priority level of this follow-up action')
    )
    
    estimated_hours = models.PositiveIntegerField(
        default=0,
        verbose_name=_('Estimated Hours'),
        help_text=_('Estimated hours to complete this action')
    )
    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='followup_actions_assigned',
        verbose_name=_('Assigned To'),
        help_text=_('Person responsible for completing this action')
    )
    
    assigned_team = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name=_('Assigned Team'),
        help_text=_('Team responsible for this action')
    )
    start_date = models.DateField(
        blank=True, 
        null=True, 
        verbose_name=_('Start Date'),
        help_text=_('Date when this action was started')
    )
    
    due_date = models.DateField(
        blank=True, 
        null=True, 
        verbose_name=_('Due Date'),
        help_text=_('Date by which this action should be completed')
    )
    
    revised_due_date = models.DateField(
        blank=True, 
        null=True, 
        verbose_name=_('Revised Due Date'),
        help_text=_('Revised date if extended')
    )
    
    extension_reason = CKEditor5Field(
        _('Extension Reason'), 
        config_name='extends', 
        blank=True, 
        null=True,
        help_text=_('Reason for extending the due date')
    )
    
    status = models.CharField(
        max_length=16, 
        choices=STATUS_CHOICES, 
        default='not_started', 
        verbose_name=_('Status'),
        help_text=_('Current status of this action')
    )
    
    completed_at = models.DateTimeField(
        blank=True, 
        null=True, 
        verbose_name=_('Completed At'),
        help_text=_('Date and time when this action was completed')
    )
    
    completed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='followup_actions_completed',
        verbose_name=_('Completed By'),
        help_text=_('Person who completed this action')
    )
    
    completion_evidence = CKEditor5Field(
        _('Completion Evidence'), 
        config_name='extends', 
        blank=True, 
        null=True,
        help_text=_('Evidence of action completion')
    )
    
    notes = CKEditor5Field(
        _('Notes'), 
        config_name='extends', 
        blank=True, 
        null=True,
        help_text=_('Additional notes about this follow-up action')
    )
    
    # Approvals for this action
    approvals = GenericRelation(
        'audit.Approval',
        content_type_field='content_type',
        object_id_field='object_id',
        related_query_name='followupaction',
        related_name='approvals',
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='followup_actions_created',
        verbose_name=_('Created By'),
        help_text=_('Person who created this action')
    )
    created_at = models.DateTimeField(auto_now_add=True)
    history = HistoricalRecords()

    class Meta:
        app_label = 'audit'
        verbose_name = _('Follow-Up Action')
        verbose_name_plural = _('Follow-Up Actions')
        ordering = ['priority', 'due_date', '-created_at']
        indexes = [
            models.Index(fields=['organization']),
            models.Index(fields=['issue']),
            models.Index(fields=['recommendation']),
            models.Index(fields=['status']),
            models.Index(fields=['priority']),
            models.Index(fields=['due_date']),
        ]
        constraints = [
            models.CheckConstraint(
                check=models.Q(organization__isnull=False),
                name='organization_required_followupaction'
            )
        ]

    def save(self, *args, **kwargs):
        # Update status if overdue
        today = date.today()
        if self.due_date and today > self.due_date and self.status not in ['completed', 'cancelled']:
            self.status = 'overdue'
            
        # Set start_date if status changes to in_progress
        if self.status == 'in_progress' and not self.start_date:
            self.start_date = today
            
        # Set completed_at if status changes to completed
        if self.status == 'completed' and not self.completed_at:
            self.completed_at = datetime.now()
            if hasattr(self, 'last_modified_by') and self.last_modified_by:
                self.completed_by = self.last_modified_by
        
        with reversion.create_revision():
            if hasattr(self, 'last_modified_by') and self.last_modified_by:
                reversion.set_user(self.last_modified_by)
            reversion.set_comment(f"Saved follow-up action '{self.title}' (Status: {self.status})")
            super().save(*args, **kwargs)
    
    def __str__(self):
        issue_ref = f"{self.issue.code}" if self.issue else "No Issue"
        return f"{self.title} - {issue_ref} ({self.get_status_display()})"
        
    def get_engagement(self):
        """Get the engagement this action is linked to via issue"""
        if self.issue:
            return self.issue.get_engagement()
        return None