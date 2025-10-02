# apps/audit/models/issue.py
# Enhanced for GIAS 2024 compliance

import reversion
from datetime import date, timedelta
from django.db import models
from django.urls import reverse
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.conf import settings
from django_ckeditor_5.fields import CKEditor5Field
from django.contrib.contenttypes.fields import GenericRelation
from django.core.validators import MinValueValidator, MaxValueValidator
from simple_history.models import HistoricalRecords

from core.models.abstract_models import OrganizationOwnedModel, AuditableModel, SoftDeletionModel
from .engagement import Engagement
from .procedure import Procedure
from core.models.validators import validate_file_extension, validate_file_size

@reversion.register()
class Issue(OrganizationOwnedModel, AuditableModel, SoftDeletionModel):
    """
    Audit issue model with FSM approval, rich-text fields, file validators, 
    and date checks. Enhanced for GIAS 2024 with comprehensive issue classification,
    tracking, and reporting capabilities.
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
        _('Related Risks'),
        config_name='extends',
        blank=True,
        null=True,
        help_text=_('Describe the risks associated with this audit finding. For organizations with robust risk management, you can also link to specific risks from the risk register via the Related Risks tab.')
    )
    linked_risks = models.ManyToManyField(
        'risk.Risk',
        related_name='audit_issues',
        blank=True,
        verbose_name=_('Linked Risks'),
        help_text=_('Link to specific risks from the organization\'s risk register')
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
        verbose_name=_('Issue Owner'),
        help_text=_('Person responsible for remediating this issue'),
    )
    secondary_owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='issues_secondary_owned',
        verbose_name=_('Secondary Owner'),
        help_text=_('Backup person responsible for this issue'),
    )
    issue_owner_email = models.EmailField(blank=True, null=True, help_text=_('If owner is not a user, enter their email here.'))
    issue_owner_title = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name=_('Issue Owner Title'),
    )
    procedure = models.ForeignKey(
        'Procedure',
        on_delete=models.CASCADE,
        related_name='issues',
        verbose_name=_('Procedure'),
        null=False,
        blank=False,
        help_text=_('The audit procedure that identified this issue')
    )
    
    # GIAS 2024 Issue Classification Fields
    ISSUE_TYPE_CHOICES = [
        ('control_deficiency', _('Control Deficiency')),
        ('significant_deficiency', _('Significant Deficiency')),
        ('material_weakness', _('Material Weakness')),
        ('compliance', _('Compliance Issue')),
        ('process_improvement', _('Process Improvement')),
        ('fraud', _('Fraud')),
        ('ethics', _('Ethics Violation')),
        ('security', _('Security Issue')),
        ('data_privacy', _('Data Privacy')),
        ('regulatory', _('Regulatory')),
        ('other', _('Other')),
    ]
    
    issue_type = models.CharField(
        max_length=30,
        choices=ISSUE_TYPE_CHOICES,
        default='control_deficiency',
        db_index=True,
        verbose_name=_('Issue Type'),
        help_text=_('Classification of the issue according to GIAS 2024 standards')
    )
    
    is_repeat_issue = models.BooleanField(
        default=False,
        verbose_name=_('Repeat Issue'),
        help_text=_('Indicates if this issue was identified in a previous audit')
    )
    
    prior_issue_reference = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        verbose_name=_('Prior Issue Reference'),
        help_text=_('Reference to previous audit issue if this is a repeat finding')
    )

    RISK_LEVEL_CHOICES = [
        ('low', _('Low')),
        ('medium', _('Medium')),
        ('high', _('High')),
        ('critical', _('Critical')),
    ]

    # GIAS 2024 Risk Assessment Matrix
    IMPACT_CHOICES = [
        (1, _('Minor')),
        (2, _('Moderate')),
        (3, _('Major')),
    ]

    LIKELIHOOD_CHOICES = [
        (1, _('Unlikely')),
        (2, _('Possible')),
        (3, _('Likely')),
    ]

    risk_level = models.CharField(
        max_length=12,
        choices=RISK_LEVEL_CHOICES,
        default='low',
        db_index=True,
        verbose_name=_("Risk Level"),
    )

    impact = models.IntegerField(
        choices=IMPACT_CHOICES,
        default=1,
        db_index=True,
        verbose_name=_("Impact"),
    )

    likelihood = models.IntegerField(
        choices=LIKELIHOOD_CHOICES,
        default=1,
        db_index=True,
        verbose_name=_("Likelihood"),
    )
    
    risk_score = models.PositiveSmallIntegerField(
        default=1,  # Default low impact (1) * low likelihood (1)
        verbose_name=_('Risk Score'),
        help_text=_('Calculated as Impact × Likelihood'),
    )
    
    # Additional GIAS 2024 assessment fields
    business_impact = CKEditor5Field(
        _('Business Impact'),
        config_name='extends',
        blank=True,
        null=True,
        help_text=_('Description of how this issue impacts the business')
    )
    
    financial_impact = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        blank=True,
        null=True,
        verbose_name=_('Financial Impact'),
        help_text=_('Estimated financial impact in monetary terms')
    )
    
    regulatory_impact = models.BooleanField(
        default=False,
        verbose_name=_('Regulatory Impact'),
        help_text=_('Indicates if this issue has regulatory implications')
    )
    
    reputational_impact = models.BooleanField(
        default=False,
        verbose_name=_('Reputational Impact'),
        help_text=_('Indicates if this issue could affect organizational reputation')
    )
    
    days_overdue = models.PositiveIntegerField(
        default=0,
        verbose_name=_('Days Overdue'),
        help_text=_('Number of days the issue is past its target or revised date')
    )

    ISSUE_STATUS_CHOICES = [
        ('draft', _('Draft')),
        ('open', _('Open')),
        ('in_progress', _('In Progress')),
        ('pending_validation', _('Pending Validation')),
        ('pending_review', _('Pending Review')),
        ('pending_approval', _('Pending Approval')),
        ('closed', _('Closed')),
        ('reopened', _('Reopened')),
        ('extended', _('Extended')),
        ('escalated', _('Escalated')),
        ('accepted_risk', _('Accepted Risk')),
        ('deferred', _('Deferred')),
        ('transferred', _('Transferred')),
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
        ('planned', _('Planned')),
        ('management_remediating', _('Management Remediating')),
        ('remediated_awaiting_verification', _('Remediated Awaiting Verification')),
        ('partially_remediated', _('Partially Remediated')),
        ('verified', _('Verified')),
        ('closed', _('Closed')),
        ('ineffective_remediation', _('Ineffective Remediation')),
    ]

    remediation_status = models.CharField(
        max_length=56,
        choices=REMEDIATION_CHOICES,
        default='open',
        db_index=True,
        verbose_name=_("Remediation Status"),
    )

    target_date = models.DateField(
        blank=True,
        null=True,
        verbose_name=_('Target Date'),
        help_text=_('Target date for remediation'),
    )
    
    remediation_plan_date = models.DateField(
        blank=True,
        null=True,
        verbose_name=_('Remediation Plan Date'),
        help_text=_('Date when the remediation plan was submitted')
    )
    
    remediation_priority = models.CharField(
        max_length=10,
        choices=[
            ('low', _('Low')),
            ('medium', _('Medium')),
            ('high', _('High')),
            ('critical', _('Critical')),
        ],
        default='medium',
        verbose_name=_('Remediation Priority'),
        help_text=_('Priority level for remediation efforts')
    )
    
    estimated_effort = models.PositiveIntegerField(
        blank=True,
        null=True,
        verbose_name=_('Estimated Effort (hours)'),
        help_text=_('Estimated hours required to remediate this issue')
    )
    
    estimated_cost = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        blank=True,
        null=True,
        verbose_name=_('Estimated Cost'),
        help_text=_('Estimated cost to remediate this issue')
    )

    revised_date = models.DateField(
        blank=True,
        null=True,
        verbose_name=_('Revised Date'),
        help_text=_('Revised target date if extended'),
    )

    extension_reason = CKEditor5Field(
        _('Extension Reason'),
        config_name='extends',
        blank=True,
        null=True,
        help_text=_('Reason for extending the target date'),
    )

    extension_approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='approved_issue_extensions',
        verbose_name=_('Extension Approved By'),
    )

    extension_approved_date = models.DateField(
        blank=True,
        null=True,
        verbose_name=_('Extension Approved Date'),
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
        help_text=_('Detailed plan from management to address the issue')
    )
    
    remediation_approach = models.CharField(
        max_length=20,
        choices=[
            ('fix', _('Fix')),
            ('mitigate', _('Mitigate')),
            ('accept', _('Accept')),
            ('transfer', _('Transfer')),
            ('avoid', _('Avoid')),
        ],
        default='fix',
        verbose_name=_('Remediation Approach'),
        help_text=_('The approach taken to address this issue')
    )
    
    verification_method = CKEditor5Field(
        _('Verification Method'),
        config_name='extends',
        blank=True,
        null=True,
        help_text=_('Method to be used to verify remediation')
    )
    
    verification_result = CKEditor5Field(
        _('Verification Result'),
        config_name='extends',
        blank=True,
        null=True,
        help_text=_('Results of remediation verification testing')
    )
    
    verification_date = models.DateField(
        blank=True,
        null=True,
        verbose_name=_('Verification Date'),
        help_text=_('Date when remediation was verified')
    )
    
    verified_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='issues_verified',
        verbose_name=_('Verified By'),
        help_text=_('Person who verified the remediation')
    )

    positive_finding_notes = CKEditor5Field(_('Positive Finding Notes'), config_name='extends', blank=True, null=True)

    approvals = GenericRelation(
        'audit.Approval',
        content_type_field='content_type',
        object_id_field='object_id',
        related_query_name='issue',
        related_name='approvals',
    )

    history = HistoricalRecords()

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
            models.Index(fields=['risk_level']),
            models.Index(fields=['remediation_status']),
            models.Index(fields=['procedure']),
            models.Index(fields=['issue_type']),
            models.Index(fields=['is_repeat_issue']),
            models.Index(fields=['remediation_priority']),
            models.Index(fields=['regulatory_impact']),
        ]
        constraints = [
            models.CheckConstraint(
                check=models.Q(organization__isnull=False),
                name='organization_required_issue'
            ),
            models.CheckConstraint(
                check=models.Q(risk_score__gte=1, risk_score__lte=9),
                name='risk_score_range_issue'
            ),
            models.CheckConstraint(
                check=models.Q(impact__gte=1, impact__lte=3),
                name='impact_range_issue'
            ),
            models.CheckConstraint(
                check=models.Q(likelihood__gte=1, likelihood__lte=3),
                name='likelihood_range_issue'
            )
        ]

    def __str__(self):
        owner_str = self.issue_owner.email if self.issue_owner else (self.issue_owner_email or 'No Owner')
        return f"{self.issue_title} ({self.issue_status}) - Owner: {owner_str}"

    def get_absolute_url(self):
        return reverse('audit:issue-detail', kwargs={'pk': self.pk})

    def save(self, *args, **kwargs):
        # Update status based on dates and conditions
        today = timezone.now().date()

        # If past target date and still open/in_progress, set to escalated
        if self.issue_status in ['open', 'in_progress'] and self.target_date and today > self.target_date:
            if not self.revised_date or today > self.revised_date:
                self.issue_status = 'escalated'

        # Set status to extended if revised_date is set and approved
        if self.revised_date and self.extension_approved_by and self.issue_status not in ['closed', 'accepted_risk']:
            self.issue_status = 'extended'
            
        # Update remediation status based on verification
        if self.verified_by and self.verification_date and self.remediation_status == 'remediated_awaiting_verification':
            self.remediation_status = 'verified'
            
        # When verification is complete and status is verified, update issue status to closed
        if self.remediation_status == 'verified' and self.issue_status not in ['closed', 'reopened']:
            self.issue_status = 'closed'
            
        # Calculate days overdue for reporting
        if self.target_date and today > self.target_date and self.issue_status not in ['closed', 'accepted_risk']:
            if self.revised_date and self.extension_approved_by:
                # Use revised date if approved
                if today > self.revised_date:
                    self.days_overdue = (today - self.revised_date).days
                else:
                    self.days_overdue = 0
            else:
                self.days_overdue = (today - self.target_date).days

        # Create detailed revision comment
        revision_comment = f"Saved issue '{self.code}' (Status: {self.issue_status}, Risk: {self.risk_level})"
        if self.remediation_status != 'open':
            revision_comment += f", Remediation: {self.get_remediation_status_display()}"
            
        with reversion.create_revision():
            if hasattr(self, 'last_modified_by') and self.last_modified_by:
                reversion.set_user(self.last_modified_by)
            reversion.set_comment(revision_comment)
            super().save(*args, **kwargs)

    def clean(self):
        # Validate target_date is not in the past for new issues
        if not self.pk and self.target_date and self.target_date < timezone.now().date():
            raise ValidationError({'target_date': _('Target date cannot be in the past for new issues.')})

        # Validate revised_date is after target_date
        if self.revised_date and self.target_date and self.revised_date <= self.target_date:
            raise ValidationError({'revised_date': _('Revised date must be after the original target date.')})

        # Ensure extension fields are properly set
        if self.revised_date and not self.extension_reason:
            raise ValidationError({'extension_reason': _('Extension reason is required when setting a revised date.')})

        # Calculate risk score from impact and likelihood
        self.risk_score = self.impact * self.likelihood

        # Set risk_level based on risk_score
        if self.risk_score <= 2:
            self.risk_level = 'low'
        elif self.risk_score <= 4:
            self.risk_level = 'medium'
        elif self.risk_score <= 6:
            self.risk_level = 'high'
        else:
            self.risk_level = 'critical'
            
        # Validate verification date and verified_by are consistent
        if bool(self.verification_date) != bool(self.verified_by):
            if not self.verification_date:
                raise ValidationError({'verification_date': _('Verification date is required when specifying who verified.')})
            else:
                raise ValidationError({'verified_by': _('Verifier is required when providing a verification date.')})
                
        # For repeat issues, ensure prior issue reference is provided
        if self.is_repeat_issue and not self.prior_issue_reference:
            raise ValidationError({'prior_issue_reference': _('Prior issue reference is required for repeat issues.')})

        # Validate dates are in logical order
        if self.target_date and self.actual_remediation_date and \
           self.actual_remediation_date < self.target_date:
            raise ValidationError(_('Actual remediation date cannot be before the deadline.'))
            
        # Validate verification date is after remediation date
        if self.verification_date and self.actual_remediation_date and \
           self.verification_date < self.actual_remediation_date:
            raise ValidationError({'verification_date': _('Verification date must be after the actual remediation date.')})
            
        # Verify that accepted risks have proper documentation
        if self.issue_status == 'accepted_risk' and not self.extension_reason:
            raise ValidationError({'extension_reason': _('Risk acceptance reason must be documented.')})

    @property
    def engagement(self):
        try:
            return self.procedure.risk.objective.engagement
        except AttributeError:
            return None
