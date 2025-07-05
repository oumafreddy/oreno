import reversion
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.conf import settings
from django.contrib.contenttypes.fields import GenericRelation
from django.core.validators import MinValueValidator, MaxValueValidator
from django.core.exceptions import ValidationError
from core.models.abstract_models import OrganizationOwnedModel, AuditableModel, SoftDeletionModel
from core.models.validators import validate_file_extension, validate_file_size
from .risk import Risk
from django_ckeditor_5.fields import CKEditor5Field
from simple_history.models import HistoricalRecords
from django.utils import timezone
from django.urls import reverse

@reversion.register()
class Procedure(OrganizationOwnedModel, AuditableModel, SoftDeletionModel):
    """
    Audit test procedure model with embedded result fields in accordance with GIAS 2024.
    Links directly to Risk rather than Objective. Provides comprehensive testing approach,
    evidence gathering, and result tracking aligned with professional audit standards.
    """
    PROCEDURE_TYPE_CHOICES = [
        ('inspection', _('Inspection')),
        ('observation', _('Observation')),
        ('inquiry', _('Inquiry')),
        ('confirmation', _('Confirmation')),
        ('reperformance', _('Reperformance')),
        ('analytical', _('Analytical Procedure')),
        ('substantive', _('Substantive Testing')),
        ('walkthrough', _('Walkthrough')),
        ('compliance', _('Compliance Test')),
    ]
    
    risk = models.ForeignKey(
        Risk,
        on_delete=models.CASCADE,
        related_name='procedures',
        verbose_name=_('Risk'),
        help_text=_('The risk this procedure is designed to test')
    )
    
    procedure_type = models.CharField(
        max_length=20,
        choices=PROCEDURE_TYPE_CHOICES,
        default='inspection',
        verbose_name=_('Procedure Type'),
        help_text=_('The type of audit procedure being performed')
    )
    title = models.CharField(
        max_length=255, 
        verbose_name=_('Procedure Title'),
        help_text=_('Test procedure title')
    )
    description = CKEditor5Field(
        _('Procedure Description'), 
        config_name='extends', 
        blank=True, 
        null=True,
        help_text=_('Detailed test steps and methodology')
    )
    
    control_being_tested = CKEditor5Field(
        _('Control Being Tested'), 
        config_name='extends', 
        blank=True, 
        null=True,
        help_text=_('Description of the specific control being evaluated')
    )
    criteria = CKEditor5Field(
        _('Audit Criteria'), 
        config_name='extends', 
        blank=True, 
        null=True,
        help_text=_('Standards, policies or benchmarks used to evaluate the control')
    )
    sample_size = models.PositiveIntegerField(
        default=0,
        verbose_name=_('Sample Size'),
        help_text=_('Number of items tested')
    )
    sampling_method = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name=_('Sampling Method'),
        help_text=_('Method used to select samples')
    )
    
    # Testing information
    planned_date = models.DateField(
        blank=True,
        null=True,
        verbose_name=_('Planned Test Date'),
        help_text=_('Date when testing is planned to be performed')
    )
    test_date = models.DateField(
        blank=True,
        null=True,
        verbose_name=_('Actual Test Date'),
        help_text=_('Date when testing was actually performed')
    )
    tested_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='procedures_tested',
        verbose_name=_('Tested By'),
        help_text=_('Auditor who performed the test')
    )
    
    estimated_hours = models.DecimalField(
        max_digits=6, 
        decimal_places=2,
        default=0,
        verbose_name=_('Estimated Hours'),
        help_text=_('Estimated time to complete this procedure')
    )
    
    actual_hours = models.DecimalField(
        max_digits=6, 
        decimal_places=2,
        default=0,
        verbose_name=_('Actual Hours'),
        help_text=_('Actual time spent on this procedure')
    )
    
    # Embedded result fields (previously in ProcedureResult model)
    STATUS_CHOICES = [
        ('not_started', _('Not Started')),
        ('planning', _('Planning')),
        ('in_progress', _('In Progress')),
        ('pending_review', _('Pending Review')),
        ('completed', _('Completed')),
        ('deferred', _('Deferred')),
        ('cancelled', _('Cancelled')),
    ]
    test_status = models.CharField(
        max_length=32,
        choices=STATUS_CHOICES,
        default='not_started',
        verbose_name=_('Test Status'),
        help_text=_('Current status of testing')
    )
    
    RESULT_CHOICES = [
        ('operating_effectively', _('Operating Effectively')),
        ('not_effective', _('Not Effective')),
        ('partially_effective', _('Partially Effective')),
        ('design_effective_operating_ineffective', _('Design Effective, Operating Ineffective')),
        ('design_ineffective', _('Design Ineffective')),
        ('inconsistent_application', _('Inconsistent Application')),
        ('not_applicable', _('Not Applicable')),
        ('not_tested', _('Not Tested')),
        ('needs_improvement', _('Needs Improvement')),
    ]
    result = models.CharField(
        max_length=40,
        choices=RESULT_CHOICES,
        blank=True,
        null=True,
        verbose_name=_('Test Result'),
        help_text=_('Outcome of the test procedure')
    )
    
    result_notes = CKEditor5Field(
        _('Result Notes'), 
        config_name='extends', 
        blank=True, 
        null=True,
        help_text=_('Detailed observations from testing')
    )
    exceptions_noted = models.PositiveIntegerField(
        default=0,
        verbose_name=_('Exceptions Noted'),
        help_text=_('Number of exceptions identified during testing')
    )
    exception_details = CKEditor5Field(
        _('Exception Details'), 
        config_name='extends', 
        blank=True, 
        null=True,
        help_text=_('Details of any exceptions identified')
    )
    conclusion = CKEditor5Field(
        _('Conclusion'), 
        config_name='extends', 
        blank=True, 
        null=True,
        help_text=_('Auditor\'s conclusion based on test results')
    )
    impact_assessment = CKEditor5Field(
        _('Impact Assessment'), 
        config_name='extends', 
        blank=True, 
        null=True,
        help_text=_('Assessment of the impact of any identified exceptions')
    )
    is_positive_finding = models.BooleanField(
        default=False,
        verbose_name=_('Positive Finding'),
        help_text=_('Indicates a positive outcome worth highlighting')
    )
    control_maturity = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        null=True,
        blank=True,
        verbose_name=_('Control Maturity'),
        help_text=_('Rating of control maturity on a scale of 1-5')
    )
    
    # Document evidence
    evidence_list = CKEditor5Field(
        _('Evidence List'), 
        config_name='extends', 
        blank=True, 
        null=True,
        help_text=_('List of evidence gathered during testing')
    )
    evidence = models.FileField(
        upload_to='audit/procedure_evidence/%Y/%m/',
        validators=[validate_file_extension, validate_file_size],
        blank=True,
        null=True,
        verbose_name=_('Primary Evidence'),
        help_text=_('Primary supporting documentation for test results')
    )
    additional_evidence = models.FileField(
        upload_to='audit/procedure_evidence/%Y/%m/',
        validators=[validate_file_extension, validate_file_size],
        blank=True,
        null=True,
        verbose_name=_('Additional Evidence'),
        help_text=_('Additional supporting documentation for test results')
    )
    
    # Review information
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='procedures_reviewed',
        verbose_name=_('Reviewed By'),
        help_text=_('Auditor who reviewed the test results')
    )
    review_date = models.DateField(
        blank=True,
        null=True,
        verbose_name=_('Review Date'),
        help_text=_('Date when the procedure was reviewed')
    )
    review_notes = CKEditor5Field(
        _('Review Notes'), 
        config_name='extends', 
        blank=True, 
        null=True,
        help_text=_('Notes from the reviewer')
    )
    
    # Approvals
    approvals = GenericRelation(
        'audit.Approval',
        content_type_field='content_type',
        object_id_field='object_id',
        related_query_name='procedure',
        related_name='approvals',
    )
    
    order = models.PositiveIntegerField(
        default=0, 
        verbose_name=_('Order'),
        help_text=_('Display order within the risk')
    )
    history = HistoricalRecords()

    class Meta:
        app_label = 'audit'
        verbose_name = _('Procedure')
        verbose_name_plural = _('Procedures')
        ordering = ['order', 'id']
        indexes = [
            models.Index(fields=['organization']),
            models.Index(fields=['risk']),
            models.Index(fields=['test_status']),
            models.Index(fields=['result']),
            models.Index(fields=['procedure_type']),
            models.Index(fields=['tested_by']),
        ]
        constraints = [
            models.CheckConstraint(
                check=models.Q(organization__isnull=False),
                name='organization_required_procedure'
            ),
            models.CheckConstraint(
                check=models.Q(exceptions_noted__gte=0),
                name='exceptions_noted_positive_procedure'
            ),
        ]
        
    def __str__(self):
        return f"{self.title} ({self.risk.objective.engagement.code})"
        
    def save(self, *args, **kwargs):
        # Automatically set organization from parent risk if not set
        if not self.organization_id and self.risk_id:
            self.organization = self.risk.organization
            
        # Set test_date to today if result is being set for the first time
        if self.result and not self.test_date:
            self.test_date = timezone.now().date()
        
        # Update test status based on conditions
        if self.result:
            if self.test_status not in ['pending_review', 'completed']:
                self.test_status = 'pending_review'
                
            # If we have a reviewer and review date, mark as completed
            if self.reviewed_by and self.review_date:
                self.test_status = 'completed'
        elif self.test_date and self.test_status == 'not_started':
            self.test_status = 'in_progress'
            
        # For operating effectiveness results, ensure no exceptions are noted
        if self.result == 'operating_effectively' and self.exceptions_noted > 0:
            raise ValidationError(_("A procedure with 'Operating Effectively' result cannot have exceptions noted."))
            
        # For not effective results, ensure exceptions are noted
        if self.result == 'not_effective' and self.exceptions_noted == 0:
            raise ValidationError(_("A procedure with 'Not Effective' result should have at least one exception noted."))
            
        # Create revision with detailed comment
        revision_comment = f"Saved procedure '{self.title}' (Status: {self.test_status})"
        if self.result:
            revision_comment += f", Result: {self.get_result_display()}"
            
        with reversion.create_revision():
            if hasattr(self, 'last_modified_by') and self.last_modified_by:
                reversion.set_user(self.last_modified_by)
            reversion.set_comment(revision_comment)
            super().save(*args, **kwargs)
            
    @property
    def objective(self):
        """Return the parent objective through the risk relationship"""
        return self.risk.objective if self.risk else None
        
    @property
    def engagement(self):
        """Return the parent engagement through the risk and objective relationship"""
        if self.risk and self.risk.objective:
            return self.risk.objective.engagement
        return None
        
    @property
    def has_issues(self):
        """Check if this procedure has any associated issues"""
        return self.issues.exists()
        
    @property
    def testing_status_summary(self):
        """Return a summary of testing status including exceptions"""
        if not self.result:
            return _('Not tested')
            
        if self.result == 'operating_effectively':
            return _('Effective (No exceptions)')
            
        if self.exceptions_noted > 0:
            return _('Exceptions: {}').format(self.exceptions_noted)
            
        return self.get_result_display()

    def get_absolute_url(self):
        """Return the absolute URL for the procedure detail view."""
        return reverse('audit:procedure-detail', kwargs={'pk': self.pk})

    @property
    def issue_count(self):
        return self.issues.count()

    @property
    def requires_issue_creation(self):
        return self.result in ['not_effective', 'partially_effective', 'design_ineffective'] and self.exceptions_noted > 0