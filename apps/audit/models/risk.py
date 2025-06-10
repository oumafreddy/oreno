import reversion
from datetime import date
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinValueValidator, MaxValueValidator
from django.contrib.contenttypes.fields import GenericRelation
from django.conf import settings
from core.models.abstract_models import OrganizationOwnedModel, AuditableModel, SoftDeletionModel
from .objective import Objective
from django_ckeditor_5.fields import CKEditor5Field
from simple_history.models import HistoricalRecords

@reversion.register()
class Risk(SoftDeletionModel):
    # Explicitly define the fields from OrganizationOwnedModel and AuditableModel
    # with unique related_name attributes to avoid conflicts with risk.Risk
    organization = models.ForeignKey(
        'organizations.Organization',
        on_delete=models.CASCADE,
        related_name='audit_risks',
        verbose_name=_('Organization'),
        help_text=_("Organization that owns this record")
    )
    
    # Timestamp fields from TimeStampedModel
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_('Created At'))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_('Updated At'))
    
    # User tracking fields from AuditableModel
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='audit_risk_created',
        verbose_name=_('Created By'),
        help_text=_("User who created this record")
    )
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='audit_risk_updated',
        verbose_name=_('Updated By'),
        help_text=_("User who last modified this record")
    )
    """
    Risk model representing identified risks associated with audit objectives.
    Conforms to GIAS 2024 risk assessment methodologies.
    """
    RISK_CATEGORY_CHOICES = [
        ('strategic', _('Strategic')),
        ('operational', _('Operational')),
        ('financial', _('Financial')),
        ('compliance', _('Compliance')),
        ('reputational', _('Reputational')),
        ('technological', _('Technological')),
        ('environmental', _('Environmental')),
        ('fraud', _('Fraud')),
        ('human_resources', _('Human Resources')),
        ('legal', _('Legal')),
        ('governance', _('Governance')),
        ('other', _('Other')),
    ]
    
    RISK_STATUS_CHOICES = [
        ('identified', _('Identified')),
        ('assessed', _('Assessed')),
        ('mitigated', _('Mitigated')),
        ('accepted', _('Accepted')),
        ('transferred', _('Transferred')),
        ('closed', _('Closed')),
    ]
    
    RISK_APPETITE_CHOICES = [
        ('averse', _('Risk Averse')),
        ('minimalist', _('Minimalist')),
        ('cautious', _('Cautious')),
        ('open', _('Open')),
        ('seeking', _('Risk Seeking')),
    ]

    organization = models.ForeignKey(
        'organizations.Organization',
        on_delete=models.CASCADE,
        related_name='audit_risk_set',
        verbose_name=_('Organization')
    )
    
    objective = models.ForeignKey(
        Objective,
        on_delete=models.CASCADE,
        related_name='audit_risks',
        verbose_name=_('Objective'),
        help_text=_('The audit objective this risk is associated with')
    )
    
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='audit_risk_created',
        verbose_name=_('Created By')
    )
    
    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='audit_risk_assigned',
        verbose_name=_('Risk Owner'),
        help_text=_('Person responsible for managing this risk')
    )
    
    title = models.CharField(
        max_length=255, 
        verbose_name=_('Risk Title'),
        help_text=_('Concise title describing the risk')
    )
    description = CKEditor5Field(
        _('Risk Description'), 
        config_name='extends', 
        blank=True, 
        null=True,
        help_text=_('Detailed description of the risk')
    )
    category = models.CharField(
        max_length=20,
        choices=RISK_CATEGORY_CHOICES,
        default='operational',
        verbose_name=_('Risk Category'),
        help_text=_('Primary category of the risk')
    )
    
    status = models.CharField(
        max_length=20,
        choices=RISK_STATUS_CHOICES,
        default='identified',
        verbose_name=_('Risk Status'),
        help_text=_('Current status in the risk management lifecycle')
    )
    
    risk_appetite = models.CharField(
        max_length=15,
        choices=RISK_APPETITE_CHOICES,
        default='cautious',
        verbose_name=_('Risk Appetite'),
        help_text=_('Organization\'s willingness to accept this type of risk')
    )
    
    risk_tolerance = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(9)],
        default=4,
        verbose_name=_('Risk Tolerance'),
        help_text=_('Maximum acceptable risk level (1-9)')
    )
    existing_controls = CKEditor5Field(
        _('Existing Controls'), 
        config_name='extends', 
        blank=True, 
        null=True,
        help_text=_('Description of controls already in place to mitigate this risk')
    )
    
    control_effectiveness = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(3)],
        default=2,
        verbose_name=_('Control Effectiveness'),
        help_text=_('Effectiveness of existing controls (1=Low, 2=Medium, 3=High)')
    )
    
    mitigation_plan = CKEditor5Field(
        _('Mitigation Plan'), 
        config_name='extends', 
        blank=True, 
        null=True,
        help_text=_('Action plan to address or mitigate this risk')
    )
    
    target_date = models.DateField(
        null=True,
        blank=True,
        verbose_name=_('Target Date'),
        help_text=_('Target date for implementing risk mitigation measures')
    )
    
    # Risk assessment using 3x3 matrix as per GIAS 2024
    likelihood = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(3)],
        default=2,
        verbose_name=_('Likelihood'),
        help_text=_('Likelihood score (1=Low, 2=Medium, 3=High)')
    )
    impact = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(3)],
        default=2,
        verbose_name=_('Impact'),
        help_text=_('Impact score (1=Low, 2=Medium, 3=High)')
    )
    inherent_risk_score = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(9)],
        default=4,
        verbose_name=_('Inherent Risk Score'),
        help_text=_('Calculated as Likelihood × Impact (1-9)')
    )
    residual_risk_score = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(9)],
        default=4,
        verbose_name=_('Residual Risk Score'),
        help_text=_('Remaining risk after considering existing controls (1-9)')
    )
    
    order = models.PositiveIntegerField(
        default=0, 
        verbose_name=_('Order'),
        help_text=_('Display order within the objective')
    )
    
    # Approvals for this risk
    approvals = GenericRelation(
        'audit.Approval',
        content_type_field='content_type',
        object_id_field='object_id',
        related_query_name='risk',
        related_name='approvals',
    )
    
    history = HistoricalRecords()

    class Meta:
        app_label = 'audit'
        verbose_name = _('Risk')
        verbose_name_plural = _('Risks')
        ordering = ['order', 'id']
        indexes = [
            models.Index(fields=['organization']),
            models.Index(fields=['objective']),
            models.Index(fields=['category']),
            models.Index(fields=['status']),
            models.Index(fields=['inherent_risk_score']),
            models.Index(fields=['residual_risk_score']),
        ]
        constraints = [
            models.CheckConstraint(
                check=models.Q(organization__isnull=False),
                name='organization_required_risk'
            ),
            models.CheckConstraint(
                check=models.Q(inherent_risk_score__lte=9, inherent_risk_score__gte=1),
                name='risk_score_range_risk'
            )
        ]
        
    def __str__(self):
        return f"{self.title} (Risk Score: {self.inherent_risk_score}/9)"
    
    def save(self, *args, **kwargs):
        # Auto-calculate inherent risk score if not explicitly set
        if not self.pk or not self.inherent_risk_score:
            self.inherent_risk_score = self.likelihood * self.impact
        # Set residual risk score based on control effectiveness
        calculated_residual = max(1, round(self.inherent_risk_score / self.control_effectiveness))
        if not self.residual_risk_score or self.residual_risk_score > self.inherent_risk_score:
            self.residual_risk_score = min(calculated_residual, self.inherent_risk_score)
        # Only auto-advance status if this is a new risk or status is not set by user
        if not self.pk:
            if self.status == 'identified' and self.inherent_risk_score:
                self.status = 'assessed'
            if self.residual_risk_score <= self.risk_tolerance and self.status == 'assessed':
                self.status = 'mitigated'
        # If updating, do not override status if set by user
        with reversion.create_revision():
            if hasattr(self, 'last_modified_by') and self.last_modified_by:
                reversion.set_user(self.last_modified_by)
            reversion.set_comment(f"Saved risk '{self.title}' (Status: {self.status})")
            super().save(*args, **kwargs)
    
    @property
    def risk_level(self):
        """Returns the risk level based on the inherent risk score"""
        if self.inherent_risk_score <= 2:
            return _('Low')
        elif self.inherent_risk_score <= 6:
            return _('Medium')
        else:
            return _('High')
            
    @property
    def within_appetite(self):
        """Returns whether the residual risk is within defined tolerance"""
        return self.residual_risk_score <= self.risk_tolerance
    
    @property
    def residual_risk_level(self):
        """Returns the residual risk level based on the residual risk score"""
        if self.residual_risk_score <= 2:
            return _('Low')
        elif self.residual_risk_score <= 6:
            return _('Medium')
        else:
            return _('High')
            
    def get_procedures(self):
        """Returns procedures linked to this risk"""
        return self.procedures.all()
        
    def get_issues(self):
        """Returns issues linked to this risk through procedures"""
        from .issue import Issue
        procedure_ids = self.procedures.values_list('id', flat=True)
        return Issue.objects.filter(procedure__in=procedure_ids)
