# oreno\apps\compliance\models.py

from django.db import models
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator, MaxValueValidator
from django_ckeditor_5.fields import CKEditor5Field
from django.utils import timezone
from core.models.validators import validate_file_extension, validate_file_size
from organizations.models import Organization
from core.models.abstract_models import TimeStampedModel, OrganizationOwnedModel, AuditableModel
from django.contrib.auth import get_user_model
from risk.models import Risk

# ----------------------
# COMPLIANCE MANAGEMENT (Risk Unit)
# ----------------------

class ComplianceFramework(OrganizationOwnedModel):
    name = models.CharField(max_length=255, db_index=True)
    description = CKEditor5Field('Description', config_name='extends', blank=True, null=True)
    version = models.CharField(max_length=50, blank=True, null=True)
    regulatory_body = models.CharField(max_length=255, blank=True, null=True)
    
    class Meta:
        unique_together = ['organization', 'name']
        indexes = [models.Index(fields=['organization', 'regulatory_body'])]
        app_label = "compliance"
        constraints = [
            models.CheckConstraint(
                check=models.Q(organization__isnull=False),
                name='organization_required_complianceframework'
            )
        ]
    
    def __str__(self):
        return f"{self.name} v{self.version or '1.0'}"

class PolicyDocument(OrganizationOwnedModel, AuditableModel):
    title = models.CharField(max_length=512, db_index=True)
    file = models.FileField(
        upload_to='policy_documents/',
        validators=[validate_file_extension, validate_file_size]
    )
    version = models.CharField(max_length=50, default='1.0')
    effective_date = models.DateField()
    expiration_date = models.DateField(null=True, blank=True)
    owner = models.ForeignKey(get_user_model(), on_delete=models.SET_NULL, null=True, blank=True,
        help_text='Select a user as owner, or leave blank to specify an email below.')
    owner_email = models.EmailField(blank=True, null=True, help_text='If owner is not a user, enter their email here.')
    is_anonymized = models.BooleanField(default=False)  # For sensitive data
    
    def __str__(self):
        owner_str = self.owner.email if self.owner else (self.owner_email or 'No Owner')
        return f"{self.title} (v{self.version}) - Owner: {owner_str}"

    class Meta:
        constraints = [
            models.CheckConstraint(
                check=models.Q(organization__isnull=False),
                name='organization_required_policydocument'
            )
        ]

class DocumentProcessing(OrganizationOwnedModel):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]
    
    document = models.ForeignKey(PolicyDocument, on_delete=models.CASCADE)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    ai_model_version = models.CharField(max_length=50, default='1.0')
    parsed_text = models.TextField(blank=True, null=True)
    error_message = models.TextField(blank=True, null=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    confidence_score = models.FloatField(default=0.0)  # 0.0 to 1.0
    
    def __str__(self):
        return f"Processing {self.document.title} ({self.status})"

    class Meta:
        constraints = [
            models.CheckConstraint(
                check=models.Q(organization__isnull=False),
                name='organization_required_documentprocessing'
            )
        ]

class ComplianceRequirement(OrganizationOwnedModel, AuditableModel):
    requirement_id = models.CharField(max_length=50, unique=True, db_index=True)
    title = models.CharField(max_length=512, db_index=True)
    description = CKEditor5Field('Description', config_name='extends', blank=True, null=True)
    
    # Source can be regulatory framework OR internal policy
    regulatory_framework = models.ForeignKey(
        ComplianceFramework, 
        on_delete=models.SET_NULL, 
        null=True, blank=True
    )
    policy_document = models.ForeignKey(
        PolicyDocument, 
        on_delete=models.SET_NULL, 
        null=True, blank=True
    )
    policy_section = models.CharField(max_length=512, blank=True, null=True)
    
    jurisdiction = models.CharField(max_length=100)
    mandatory = models.BooleanField(default=True)
    tags = models.JSONField(default=dict, blank=True)  # e.g., {"category": "data privacy", "risk_level": "high"}
    
    class Meta:
        ordering = ['requirement_id']
        indexes = [
            models.Index(fields=['regulatory_framework']),
            models.Index(fields=['policy_document']),
        ]
        app_label = "compliance"
        constraints = [
            models.CheckConstraint(
                check=models.Q(organization__isnull=False),
                name='organization_required_compliancerequirement'
            )
        ]
    
    def __str__(self):
        return f"{self.requirement_id}: {self.title}"

class ComplianceObligation(OrganizationOwnedModel, AuditableModel):
    STATUS_CHOICES = [
        ('open', 'Open'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('overdue', 'Overdue'),
        ('cancelled', 'Cancelled'),
    ]
    
    obligation_id = models.CharField(max_length=50, db_index=True)
    requirement = models.ForeignKey(ComplianceRequirement, on_delete=models.CASCADE)
    description = CKEditor5Field('Description', config_name='extends', blank=True, null=True)
    due_period = models.CharField(max_length=50)
    evidence_required = models.BooleanField(default=True)
    owner = models.ForeignKey(get_user_model(), on_delete=models.SET_NULL, null=True, blank=True,
        help_text='Select a user as owner, or leave blank to specify an email below.')
    owner_email = models.EmailField(blank=True, null=True, help_text='If owner is not a user, enter their email here.')
    priority = models.IntegerField(default=3, validators=[MinValueValidator(1), MaxValueValidator(5)])
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='open')
    due_date = models.DateField(db_index=True)
    completion_date = models.DateField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    
    # Link to Risk Management
    risk = models.ForeignKey('risk.Risk', on_delete=models.SET_NULL, null=True, blank=True)
    
    class Meta:
        unique_together = ('requirement', 'obligation_id')
        indexes = [
            models.Index(fields=['due_date']),
            models.Index(fields=['status']),
        ]
        app_label = "compliance"
        constraints = [
            models.CheckConstraint(
                check=models.Q(organization__isnull=False),
                name='organization_required_complianceobligation'
            )
        ]
    
    def __str__(self):
        owner_str = self.owner.email if self.owner else (self.owner_email or 'No Owner')
        return f"{self.obligation_id}: {self.requirement.title} - Owner: {owner_str}"
    
    def check_overdue(self):
        return self.status != 'completed' and self.due_date < timezone.now().date()

class ComplianceEvidence(OrganizationOwnedModel, AuditableModel):
    obligation = models.ForeignKey(ComplianceObligation, on_delete=models.CASCADE)
    document = models.ForeignKey(PolicyDocument, on_delete=models.CASCADE)
    validity_start = models.DateField()
    validity_end = models.DateField()
    notes = CKEditor5Field('Notes', config_name='extends', blank=True, null=True)
    
    class Meta:
        indexes = [
            models.Index(fields=['validity_start', 'validity_end']),
        ]
        app_label = "compliance"
        constraints = [
            models.CheckConstraint(
                check=models.Q(organization__isnull=False),
                name='organization_required_complianceevidence'
            )
        ]
    
    def __str__(self):
        return f"Evidence for {self.obligation.obligation_id}"