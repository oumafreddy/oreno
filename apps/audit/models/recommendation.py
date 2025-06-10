import reversion
from datetime import date
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.conf import settings
from django.contrib.contenttypes.fields import GenericRelation
from core.models.abstract_models import OrganizationOwnedModel, AuditableModel, SoftDeletionModel
from .issue import Issue
from django_ckeditor_5.fields import CKEditor5Field
from simple_history.models import HistoricalRecords

@reversion.register()
class Recommendation(OrganizationOwnedModel, AuditableModel, SoftDeletionModel):
    """Recommendation model for GIAS 2024 compliance.
    Links to Issue and contains details about recommendations to address audit issues.
    """
    issue = models.ForeignKey(
        Issue,
        on_delete=models.CASCADE,
        related_name='recommendations',
        verbose_name=_('Issue'),
    )
    title = models.CharField(
        max_length=255, 
        verbose_name=_('Recommendation Title'),
        help_text=_('Title of the recommendation')
    )
    description = CKEditor5Field(
        _('Recommendation Description'), 
        config_name='extends', 
        blank=True, 
        null=True,
        help_text=_('Detailed description of the recommendation')
    )
    
    PRIORITY_CHOICES = [
        ('low', _('Low')),
        ('medium', _('Medium')),
        ('high', _('High')),
        ('critical', _('Critical')),
    ]
    
    priority = models.CharField(
        max_length=10,
        choices=PRIORITY_CHOICES,
        default='medium',
        verbose_name=_('Priority'),
        help_text=_('Priority level of this recommendation')
    )
    
    # GIAS 2024 compliance fields
    cost_benefit_analysis = CKEditor5Field(
        _('Cost-Benefit Analysis'), 
        config_name='extends', 
        blank=True, 
        null=True,
        help_text=_('Analysis of costs and benefits of implementing this recommendation')
    )
    
    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='recommendations_assigned',
        verbose_name=_('Assigned To'),
        help_text=_('Person responsible for implementing this recommendation')
    )
    
    estimated_hours = models.PositiveIntegerField(
        default=0,
        verbose_name=_('Estimated Hours'),
        help_text=_('Estimated hours to implement this recommendation')
    )
    
    estimated_cost = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        verbose_name=_('Estimated Cost'),
        help_text=_('Estimated cost to implement this recommendation')
    )
    
    order = models.PositiveIntegerField(
        default=0, 
        verbose_name=_('Order'),
        help_text=_('Display order within the issue')
    )
    # Enhanced remediation fields for GIAS 2024
    IMPLEMENTATION_STATUS_CHOICES = [
        ('not_started', _('Not Started')),
        ('in_progress', _('In Progress')),
        ('implemented', _('Implemented')),
        ('verified', _('Verified')),
        ('accepted_risk', _('Risk Accepted')),
        ('rejected', _('Rejected')),
        ('deferred', _('Deferred')),
    ]
    
    implementation_status = models.CharField(
        max_length=20, 
        choices=IMPLEMENTATION_STATUS_CHOICES, 
        default='not_started', 
        db_index=True, 
        verbose_name=_('Implementation Status'),
        help_text=_('Current status of recommendation implementation')
    )
    
    target_date = models.DateField(
        blank=True, 
        null=True, 
        verbose_name=_('Target Date'),
        help_text=_('Target date for implementing this recommendation')
    )
    
    revised_date = models.DateField(
        blank=True, 
        null=True, 
        verbose_name=_('Revised Date'),
        help_text=_('Revised target date if extended')
    )
    
    extension_reason = CKEditor5Field(
        _('Extension Reason'), 
        config_name='extends', 
        blank=True, 
        null=True,
        help_text=_('Reason for extending the target date')
    )
    
    implementation_date = models.DateField(
        blank=True, 
        null=True, 
        verbose_name=_('Implementation Date'),
        help_text=_('Date when this recommendation was implemented')
    )
    
    verification_date = models.DateField(
        blank=True, 
        null=True, 
        verbose_name=_('Verification Date'),
        help_text=_('Date when implementation was verified')
    )
    
    verified_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='recommendations_verified',
        verbose_name=_('Verified By'),
        help_text=_('Person who verified the implementation')
    )
    
    management_action_plan = CKEditor5Field(
        _('Management Action Plan'), 
        config_name='extends', 
        blank=True, 
        null=True,
        help_text=_('Detailed plan for implementing this recommendation')
    )
    
    effectiveness_evaluation = CKEditor5Field(
        _('Effectiveness Evaluation'), 
        config_name='extends', 
        blank=True, 
        null=True,
        help_text=_('Evaluation of how effective the implemented recommendation is')
    )
    
    EFFECTIVENESS_RATING_CHOICES = [
        ('not_evaluated', _('Not Evaluated')),
        ('ineffective', _('Ineffective')),
        ('partially_effective', _('Partially Effective')),
        ('effective', _('Effective')),
        ('highly_effective', _('Highly Effective')),
    ]
    
    effectiveness_rating = models.CharField(
        max_length=20, 
        choices=EFFECTIVENESS_RATING_CHOICES, 
        default='not_evaluated', 
        verbose_name=_('Effectiveness Rating'),
        help_text=_('Rating of the effectiveness of this recommendation')
    )
    # Approvals for this recommendation
    approvals = GenericRelation(
        'audit.Approval',
        content_type_field='content_type',
        object_id_field='object_id',
        related_query_name='recommendation',
        related_name='approvals',
    )
    
    # Add history tracking
    history = HistoricalRecords()

    class Meta:
        app_label = 'audit'
        verbose_name = _('Recommendation')
        verbose_name_plural = _('Recommendations')
        ordering = ['order', 'priority', 'id']
        indexes = [
            models.Index(fields=['organization']),
            models.Index(fields=['issue']),
            models.Index(fields=['implementation_status']),
            models.Index(fields=['priority']),
        ]
        constraints = [
            models.CheckConstraint(
                check=models.Q(organization__isnull=False),
                name='organization_required_recommendation'
            )
        ]

    def save(self, *args, **kwargs):
        # Set implementation_date if status changes to implemented
        if self.implementation_status == 'implemented' and not self.implementation_date:
            self.implementation_date = date.today()
            
        # Set verification_date if status changes to verified
        if self.implementation_status == 'verified' and not self.verification_date:
            self.verification_date = date.today()
            if hasattr(self, 'last_modified_by') and self.last_modified_by:
                self.verified_by = self.last_modified_by
        
        with reversion.create_revision():
            if hasattr(self, 'last_modified_by') and self.last_modified_by:
                reversion.set_user(self.last_modified_by)
            reversion.set_comment(f"Saved recommendation '{self.title}' (Status: {self.implementation_status})")
            super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.title} (Issue: {self.issue}, Status: {self.implementation_status})"