# oreno\apps\contracts\models.py

from django.db import models
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator, MaxValueValidator
from django_ckeditor_5.fields import CKEditor5Field
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.urls import reverse
from django.utils.functional import cached_property
import json
from datetime import timedelta
from core.models.validators import validate_file_extension, validate_file_size
from django.conf import settings
from organizations.models import Organization
from core.models.abstract_models import TimeStampedModel, OrganizationOwnedModel, AuditableModel
from compliance.models import ComplianceObligation

# ----------------------
# CONTRACTS MANAGEMENT (Legal Unit)
# ----------------------

class ContractType(OrganizationOwnedModel):
    name = models.CharField(max_length=150, db_index=True)
    description = CKEditor5Field('Description', config_name='extends', blank=True, null=True)
    template_file = models.FileField(
        upload_to='contract_templates/', 
        validators=[validate_file_extension, validate_file_size],
        null=True, blank=True
    )
    is_standard_template = models.BooleanField(default=False)
    
    class Meta:
        unique_together = ['organization', 'name']
        indexes = [models.Index(fields=['organization', 'is_standard_template'])]
        app_label = "contracts"
        constraints = [
            models.CheckConstraint(
                check=models.Q(organization__isnull=False),
                name='organization_required_contracttype'
            )
        ]
    
    def __str__(self):
        return f"{self.name} ({self.organization.code})"

class Party(OrganizationOwnedModel, AuditableModel):
    PARTY_TYPES = [
        ('internal', 'Internal Entity'),
        ('external', 'External Counterparty'),
        ('government', 'Government Agency'),
        ('third_party', 'Third Party Service Provider'),
    ]
    
    name = models.CharField(max_length=255, db_index=True)
    party_type = models.CharField(max_length=20, choices=PARTY_TYPES)
    legal_entity_name = models.CharField(max_length=255)
    registration_number = models.CharField(max_length=50, blank=True, null=True)
    address = CKEditor5Field('Address', config_name='extends', blank=True, null=True)
    contact_person = models.CharField(max_length=100, blank=True, null=True)
    contact_email = models.EmailField(blank=True, null=True)
    contact_phone = models.CharField(max_length=20, blank=True, null=True)
    
    class Meta:
        unique_together = ['organization', 'name']
        indexes = [models.Index(fields=['organization', 'party_type'])]
        app_label = "contracts"
        constraints = [
            models.CheckConstraint(
                check=models.Q(organization__isnull=False),
                name='organization_required_party'
            )
        ]
    
    def __str__(self):
        return f"{self.name} ({self.get_party_type_display()}) - {self.organization.code}"

class Contract(OrganizationOwnedModel, AuditableModel):
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('active', 'Active'),
        ('suspended', 'Suspended'),
        ('renewal_pending', 'Renewal Pending'),
        ('expired', 'Expired'),
        ('terminated', 'Terminated'),
    ]
    
    contract_type = models.ForeignKey(ContractType, on_delete=models.PROTECT)
    parties = models.ManyToManyField('Party', through='ContractParty', related_name='contracts')
    code = models.CharField(max_length=50, unique=True, db_index=True)
    title = models.CharField(max_length=512, db_index=True)
    description = CKEditor5Field('Description', config_name='extends', blank=True, null=True)
    
    # Timeline
    start_date = models.DateField(db_index=True)
    end_date = models.DateField(db_index=True)
    auto_renew = models.BooleanField(default=False)
    
    # Financials
    value = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    currency = models.CharField(max_length=3, default='USD')
    payment_terms = CKEditor5Field('Payment Terms', config_name='extends', blank=True, null=True)
    
    # Legal
    governing_law = models.CharField(max_length=100)
    jurisdiction = models.CharField(max_length=100)
    termination_clause = CKEditor5Field('Termination Clause', config_name='extends', blank=True, null=True)
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft', db_index=True)
    termination_date = models.DateField(null=True, blank=True)
    
    # Integration
    compliance_obligations = models.ManyToManyField(
        'compliance.ComplianceObligation',
        related_name='linked_contracts',
        blank=True
    )
    
    class Meta:
        indexes = [
            models.Index(fields=['organization', 'status']),
            models.Index(fields=['start_date', 'end_date']),
        ]
        app_label = "contracts"
        constraints = [
            models.CheckConstraint(
                check=models.Q(organization__isnull=False),
                name='organization_required_contract'
            )
        ]
    
    def __str__(self):
        return f"{self.code}: {self.title} ({self.get_status_display()})"
    
    @property
    def days_to_expiry(self):
        return (self.end_date - timezone.now().date()).days
    
    def is_overdue(self):
        return self.end_date < timezone.now().date() and self.status == 'active'
    
    def get_active_obligations(self):
        return self.compliance_obligations.filter(is_active=True)

class ContractParty(models.Model):
    contract = models.ForeignKey(Contract, on_delete=models.CASCADE)
    party = models.ForeignKey(Party, on_delete=models.CASCADE)
    is_primary_party = models.BooleanField(default=False)
    role_in_contract = models.CharField(max_length=100)
    
    class Meta:
        unique_together = ('contract', 'party')
        app_label = "contracts"
    
    def __str__(self):
        return f"{self.party.name} - {self.role_in_contract}"

class ContractMilestone(OrganizationOwnedModel, AuditableModel):
    MILESTONE_TYPES = [
        ('delivery', 'Delivery Date'),
        ('payment', 'Payment Due'),
        ('review', 'Review Period'),
        ('renewal', 'Renewal Notice'),
        ('reporting', 'Reporting Deadline'),
    ]
    
    contract = models.ForeignKey(Contract, on_delete=models.CASCADE, related_name='milestones')
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    milestone_type = models.CharField(max_length=20, choices=MILESTONE_TYPES)
    due_date = models.DateField(db_index=True)
    completion_date = models.DateField(null=True, blank=True)
    is_completed = models.BooleanField(default=False)
    reminder_days = models.IntegerField(default=7)
    
    class Meta:
        indexes = [
            models.Index(fields=['contract', 'milestone_type']),
            models.Index(fields=['due_date']),
        ]
        app_label = "contracts"
        constraints = [
            models.CheckConstraint(
                check=models.Q(organization__isnull=False),
                name='organization_required_contractmilestone'
            )
        ]
    
    def __str__(self):
        return f"{self.contract.code}: {self.title} ({self.get_milestone_type_display()})"
    
    def check_overdue(self):
        return not self.is_completed and self.due_date < timezone.now().date()
