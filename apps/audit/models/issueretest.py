import reversion
from datetime import date
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
class IssueRetest(OrganizationOwnedModel, AuditableModel, SoftDeletionModel):
    """Issue retest model for GIAS 2024 compliance.
    Used to track the verification process of implemented recommendations.
    """
    RESULT_CHOICES = [
        ('pass', _('Pass')),
        ('fail', _('Fail')),
        ('partially_effective', _('Partially Effective')),
        ('pending_testing', _('Pending Testing')),
        ('blocked', _('Blocked')),
        ('not_applicable', _('Not Applicable')),
    ]
    issue = models.ForeignKey(
        Issue,
        on_delete=models.CASCADE,
        related_name='retests',
        verbose_name=_('Issue'),
        null=True,
        blank=True,
    )
    scheduled_date = models.DateField(
        verbose_name=_('Scheduled Date'),
        null=True, 
        blank=True,
        help_text=_('Date when retest is scheduled to occur')
    )
    
    retest_date = models.DateField(
        verbose_name=_('Retest Date'), 
        null=True, 
        blank=True,
        help_text=_('Date when retest was actually performed')
    )
    
    retested_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='issue_retests',
        verbose_name=_('Retested By'),
        help_text=_('Person who performed the retest')
    )
    
    result = models.CharField(
        max_length=20, 
        choices=RESULT_CHOICES, 
        default='pending_testing',
        verbose_name=_('Retest Result'), 
        help_text=_('Result of the retest verification')
    )
    
    test_approach = CKEditor5Field(
        _('Test Approach'), 
        config_name='extends', 
        blank=True, 
        null=True,
        help_text=_('Description of the testing approach used')
    )
    
    test_evidence = CKEditor5Field(
        _('Test Evidence'), 
        config_name='extends', 
        blank=True, 
        null=True,
        help_text=_('Evidence collected during the retest')
    )
    
    notes = CKEditor5Field(
        _('Retest Notes'), 
        config_name='extends', 
        blank=True, 
        null=True,
        help_text=_('Additional notes about the retest')
    )
    
    VERIFICATION_STATUS_CHOICES = [
        ('scheduled', _('Scheduled')),
        ('in_progress', _('In Progress')),
        ('completed', _('Completed')),
        ('rescheduled', _('Rescheduled')),
        ('cancelled', _('Cancelled')),
    ]
    
    verification_status = models.CharField(
        max_length=20, 
        choices=VERIFICATION_STATUS_CHOICES, 
        default='scheduled',
        verbose_name=_('Verification Status'),
        help_text=_('Current status of the verification process')
    )
    
    reviewer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='retest_reviews',
        verbose_name=_('Reviewer'),
        help_text=_('Person who reviewed the retest results')
    )
    
    review_date = models.DateField(
        verbose_name=_('Review Date'), 
        null=True, 
        blank=True,
        help_text=_('Date when retest results were reviewed')
    )
    
    # Approvals for this retest
    approvals = GenericRelation(
        'audit.Approval',
        content_type_field='content_type',
        object_id_field='object_id',
        related_query_name='issueretest',
        related_name='approvals',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    history = HistoricalRecords()

    class Meta:
        app_label = 'audit'
        verbose_name = _('Issue Retest')
        verbose_name_plural = _('Issue Retests')
        ordering = ['-retest_date', '-created_at']
        indexes = [
            models.Index(fields=['organization']),
            models.Index(fields=['issue']),
            models.Index(fields=['result']),
            models.Index(fields=['verification_status']),
        ]
        constraints = [
            models.CheckConstraint(
                check=models.Q(organization__isnull=False),
                name='organization_required_issueretest'
            )
        ]

    def save(self, *args, **kwargs):
        # Update verification_status based on dates and result
        if self.retest_date and not self.result == 'pending_testing':
            self.verification_status = 'completed'
        elif self.retest_date and self.result == 'pending_testing':
            self.verification_status = 'in_progress'
            
        # Set review_date if reviewer is added
        if self.reviewer and not self.review_date:
            self.review_date = date.today()
            
        with reversion.create_revision():
            if hasattr(self, 'last_modified_by') and self.last_modified_by:
                reversion.set_user(self.last_modified_by)
            reversion.set_comment(f"Saved issue retest for '{self.issue.code}' (Result: {self.result})")
            super().save(*args, **kwargs)
    
    def __str__(self):
        return f"Retest of {self.issue.code} - {self.get_result_display()} on {self.retest_date or 'scheduled'}"
        
    def get_engagement(self):
        """Get the engagement this retest is linked to via issue -> procedure -> risk -> objective -> engagement"""
        return self.issue.get_engagement()