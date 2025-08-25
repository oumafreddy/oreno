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

class ISMSFramework(OrganizationOwnedModel, AuditableModel):
    """
    ISO 27001 Information Security Management System framework
    """
    name = models.CharField(max_length=255, db_index=True)
    version = models.CharField(max_length=50, default='2022')
    certification_status = models.CharField(
        max_length=20,
        choices=[
            ('not_certified', 'Not Certified'),
            ('in_progress', 'Certification in Progress'),
            ('certified', 'Certified'),
            ('maintenance', 'Maintenance Phase'),
        ],
        default='not_certified'
    )
    certification_date = models.DateField(null=True, blank=True)
    next_audit_date = models.DateField(null=True, blank=True)
    scope = CKEditor5Field('Scope', config_name='extends', blank=True, null=True)
    information_security_policy = CKEditor5Field('Information Security Policy', config_name='extends', blank=True, null=True)
    
    class Meta:
        verbose_name = "ISMS Framework"
        verbose_name_plural = "ISMS Frameworks"
        constraints = [
            models.CheckConstraint(
                check=models.Q(organization__isnull=False),
                name='organization_required_ismsframework'
            )
        ]

class InformationAsset(OrganizationOwnedModel, AuditableModel):
    """
    ISO 27001 Information Asset classification and management
    """
    ASSET_TYPE_CHOICES = [
        ('data', 'Data'),
        ('software', 'Software'),
        ('hardware', 'Hardware'),
        ('personnel', 'Personnel'),
        ('facilities', 'Facilities'),
        ('services', 'Services'),
    ]
    
    CONFIDENTIALITY_CHOICES = [
        ('public', 'Public'),
        ('internal', 'Internal'),
        ('confidential', 'Confidential'),
        ('restricted', 'Restricted'),
    ]
    
    INTEGRITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('critical', 'Critical'),
    ]
    
    AVAILABILITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('critical', 'Critical'),
    ]
    
    name = models.CharField(max_length=255, db_index=True)
    description = CKEditor5Field('Description', config_name='extends', blank=True, null=True)
    asset_type = models.CharField(max_length=20, choices=ASSET_TYPE_CHOICES)
    confidentiality = models.CharField(max_length=20, choices=CONFIDENTIALITY_CHOICES)
    integrity = models.CharField(max_length=20, choices=INTEGRITY_CHOICES)
    availability = models.CharField(max_length=20, choices=AVAILABILITY_CHOICES)
    owner = models.ForeignKey(get_user_model(), on_delete=models.SET_NULL, null=True, blank=True)
    location = models.CharField(max_length=255, blank=True, null=True)
    classification_date = models.DateField(auto_now_add=True)
    review_date = models.DateField(null=True, blank=True)
    
    class Meta:
        verbose_name = "Information Asset"
        verbose_name_plural = "Information Assets"
        constraints = [
            models.CheckConstraint(
                check=models.Q(organization__isnull=False),
                name='organization_required_informationasset'
            )
        ]

class SecurityIncident(OrganizationOwnedModel, AuditableModel):
    """
    ISO 27001 Security Incident Management
    """
    SEVERITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('critical', 'Critical'),
    ]
    
    STATUS_CHOICES = [
        ('open', 'Open'),
        ('investigating', 'Investigating'),
        ('contained', 'Contained'),
        ('resolved', 'Resolved'),
        ('closed', 'Closed'),
    ]
    
    incident_number = models.CharField(max_length=50, unique=True, db_index=True)
    title = models.CharField(max_length=255, db_index=True)
    description = CKEditor5Field('Description', config_name='extends', blank=True, null=True)
    severity = models.CharField(max_length=20, choices=SEVERITY_CHOICES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='open')
    detected_date = models.DateTimeField(auto_now_add=True)
    reported_by = models.ForeignKey(get_user_model(), on_delete=models.SET_NULL, null=True, related_name='reported_incidents')
    assigned_to = models.ForeignKey(get_user_model(), on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_incidents')
    affected_assets = models.ManyToManyField(InformationAsset, blank=True)
    containment_actions = CKEditor5Field('Containment Actions', config_name='extends', blank=True, null=True)
    resolution_actions = CKEditor5Field('Resolution Actions', config_name='extends', blank=True, null=True)
    lessons_learned = CKEditor5Field('Lessons Learned', config_name='extends', blank=True, null=True)
    resolved_date = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        verbose_name = "Security Incident"
        verbose_name_plural = "Security Incidents"
        constraints = [
            models.CheckConstraint(
                check=models.Q(organization__isnull=False),
                name='organization_required_securityincident'
            )
        ]

class PrivacyFramework(OrganizationOwnedModel, AuditableModel):
    """
    GDPR and Privacy Compliance Framework
    """
    name = models.CharField(max_length=255, db_index=True)
    version = models.CharField(max_length=50, default='GDPR 2018')
    applicable_regulations = models.JSONField(default=list, blank=True)  # ['GDPR', 'CCPA', 'LGPD']
    data_protection_officer = models.ForeignKey(get_user_model(), on_delete=models.SET_NULL, null=True, blank=True)
    privacy_policy_url = models.URLField(blank=True, null=True)
    data_retention_policy = CKEditor5Field('Data Retention Policy', config_name='extends', blank=True, null=True)
    
    class Meta:
        verbose_name = "Privacy Framework"
        verbose_name_plural = "Privacy Frameworks"
        constraints = [
            models.CheckConstraint(
                check=models.Q(organization__isnull=False),
                name='organization_required_privacyframework'
            )
        ]

class DataSubject(OrganizationOwnedModel, AuditableModel):
    """
    GDPR Data Subject Rights Management
    """
    RIGHTS_CHOICES = [
        ('access', 'Right of Access'),
        ('rectification', 'Right of Rectification'),
        ('erasure', 'Right of Erasure'),
        ('portability', 'Right of Data Portability'),
        ('restriction', 'Right of Restriction'),
        ('objection', 'Right of Objection'),
        ('automated_decision', 'Right to Automated Decision Making'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('rejected', 'Rejected'),
    ]
    
    request_id = models.CharField(max_length=50, unique=True, db_index=True)
    data_subject_email = models.EmailField()
    data_subject_name = models.CharField(max_length=255)
    right_requested = models.CharField(max_length=20, choices=RIGHTS_CHOICES)
    description = CKEditor5Field('Request Description', config_name='extends', blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    request_date = models.DateTimeField(auto_now_add=True)
    due_date = models.DateTimeField(null=True, blank=True)
    completed_date = models.DateTimeField(null=True, blank=True)
    assigned_to = models.ForeignKey(get_user_model(), on_delete=models.SET_NULL, null=True, blank=True)
    response_details = CKEditor5Field('Response Details', config_name='extends', blank=True, null=True)
    
    class Meta:
        verbose_name = "Data Subject Request"
        verbose_name_plural = "Data Subject Requests"
        constraints = [
            models.CheckConstraint(
                check=models.Q(organization__isnull=False),
                name='organization_required_datasubject'
            )
        ]

class DataProcessingActivity(OrganizationOwnedModel, AuditableModel):
    """
    GDPR Article 30 - Records of Processing Activities
    """
    LEGAL_BASIS_CHOICES = [
        ('consent', 'Consent'),
        ('contract', 'Contract'),
        ('legal_obligation', 'Legal Obligation'),
        ('vital_interests', 'Vital Interests'),
        ('public_task', 'Public Task'),
        ('legitimate_interests', 'Legitimate Interests'),
    ]
    
    name = models.CharField(max_length=255, db_index=True)
    description = CKEditor5Field('Description', config_name='extends', blank=True, null=True)
    purpose = CKEditor5Field('Purpose', config_name='extends', blank=True, null=True)
    legal_basis = models.CharField(max_length=20, choices=LEGAL_BASIS_CHOICES)
    data_categories = models.JSONField(default=list, blank=True)  # ['personal_data', 'sensitive_data']
    data_subject_categories = models.JSONField(default=list, blank=True)  # ['employees', 'customers', 'suppliers']
    recipients = models.JSONField(default=list, blank=True)  # ['internal', 'external_partners']
    retention_period = models.CharField(max_length=100, blank=True, null=True)
    security_measures = CKEditor5Field('Security Measures', config_name='extends', blank=True, null=True)
    data_transfers = models.BooleanField(default=False)
    transfer_countries = models.JSONField(default=list, blank=True)
    
    class Meta:
        verbose_name = "Data Processing Activity"
        verbose_name_plural = "Data Processing Activities"
        constraints = [
            models.CheckConstraint(
                check=models.Q(organization__isnull=False),
                name='organization_required_dataprocessingactivity'
            )
        ]

class DataBreach(OrganizationOwnedModel, AuditableModel):
    """
    GDPR Article 33 - Personal Data Breach Notification
    """
    SEVERITY_CHOICES = [
        ('low', 'Low Risk'),
        ('medium', 'Medium Risk'),
        ('high', 'High Risk'),
    ]
    
    STATUS_CHOICES = [
        ('detected', 'Detected'),
        ('investigating', 'Investigating'),
        ('contained', 'Contained'),
        ('assessed', 'Risk Assessed'),
        ('notified', 'Notified Authorities'),
        ('closed', 'Closed'),
    ]
    
    breach_id = models.CharField(max_length=50, unique=True, db_index=True)
    title = models.CharField(max_length=255, db_index=True)
    description = CKEditor5Field('Description', config_name='extends', blank=True, null=True)
    detected_date = models.DateTimeField(auto_now_add=True)
    breach_date = models.DateTimeField(null=True, blank=True)
    severity = models.CharField(max_length=20, choices=SEVERITY_CHOICES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='detected')
    affected_data_subjects = models.PositiveIntegerField(default=0)
    data_categories_affected = models.JSONField(default=list, blank=True)
    containment_actions = CKEditor5Field('Containment Actions', config_name='extends', blank=True, null=True)
    notification_date = models.DateTimeField(null=True, blank=True)
    notification_details = CKEditor5Field('Notification Details', config_name='extends', blank=True, null=True)
    
    class Meta:
        verbose_name = "Data Breach"
        verbose_name_plural = "Data Breaches"
        constraints = [
            models.CheckConstraint(
                check=models.Q(organization__isnull=False),
                name='organization_required_databreach'
            )
        ]

class FinancialControlFramework(OrganizationOwnedModel, AuditableModel):
    """
    SOX Financial Control Framework
    """
    name = models.CharField(max_length=255, db_index=True)
    fiscal_year = models.PositiveIntegerField()
    framework_type = models.CharField(
        max_length=20,
        choices=[
            ('sox', 'Sarbanes-Oxley (SOX)'),
            ('ifrs', 'International Financial Reporting Standards'),
            ('gaap', 'Generally Accepted Accounting Principles'),
            ('internal', 'Internal Financial Controls'),
        ]
    )
    control_objectives = CKEditor5Field('Control Objectives', config_name='extends', blank=True, null=True)
    testing_frequency = models.CharField(
        max_length=20,
        choices=[
            ('continuous', 'Continuous'),
            ('monthly', 'Monthly'),
            ('quarterly', 'Quarterly'),
            ('annually', 'Annually'),
        ],
        default='quarterly'
    )
    
    class Meta:
        verbose_name = "Financial Control Framework"
        verbose_name_plural = "Financial Control Frameworks"
        constraints = [
            models.CheckConstraint(
                check=models.Q(organization__isnull=False),
                name='organization_required_financialcontrolframework'
            )
        ]

class FinancialControl(OrganizationOwnedModel, AuditableModel):
    """
    SOX Financial Control Testing
    """
    CONTROL_TYPE_CHOICES = [
        ('preventive', 'Preventive'),
        ('detective', 'Detective'),
        ('corrective', 'Corrective'),
    ]
    
    CONTROL_CATEGORY_CHOICES = [
        ('authorization', 'Authorization'),
        ('segregation', 'Segregation of Duties'),
        ('access', 'Access Control'),
        ('reconciliation', 'Reconciliation'),
        ('review', 'Review and Approval'),
        ('documentation', 'Documentation'),
    ]
    
    framework = models.ForeignKey(FinancialControlFramework, on_delete=models.CASCADE)
    control_id = models.CharField(max_length=50, db_index=True)
    control_name = models.CharField(max_length=255, db_index=True)
    control_description = CKEditor5Field('Control Description', config_name='extends', blank=True, null=True)
    control_type = models.CharField(max_length=20, choices=CONTROL_TYPE_CHOICES)
    control_category = models.CharField(max_length=20, choices=CONTROL_CATEGORY_CHOICES)
    control_owner = models.ForeignKey(get_user_model(), on_delete=models.SET_NULL, null=True, blank=True)
    financial_process = models.CharField(max_length=255, blank=True, null=True)
    risk_assessment = CKEditor5Field('Risk Assessment', config_name='extends', blank=True, null=True)
    control_procedure = CKEditor5Field('Control Procedure', config_name='extends', blank=True, null=True)
    testing_frequency = models.CharField(
        max_length=20,
        choices=[
            ('continuous', 'Continuous'),
            ('monthly', 'Monthly'),
            ('quarterly', 'Quarterly'),
            ('annually', 'Annually'),
        ]
    )
    last_tested_date = models.DateField(null=True, blank=True)
    next_test_date = models.DateField(null=True, blank=True)
    
    class Meta:
        verbose_name = "Financial Control"
        verbose_name_plural = "Financial Controls"
        constraints = [
            models.CheckConstraint(
                check=models.Q(organization__isnull=False),
                name='organization_required_financialcontrol'
            )
        ]

class FinancialControlTest(OrganizationOwnedModel, AuditableModel):
    """
    Financial Control Testing Results
    """
    TEST_RESULT_CHOICES = [
        ('effective', 'Effective'),
        ('ineffective', 'Ineffective'),
        ('partially_effective', 'Partially Effective'),
        ('not_tested', 'Not Tested'),
    ]
    
    control = models.ForeignKey(FinancialControl, on_delete=models.CASCADE)
    test_id = models.CharField(max_length=50, unique=True, db_index=True)
    test_date = models.DateField(auto_now_add=True)
    tested_by = models.ForeignKey(get_user_model(), on_delete=models.SET_NULL, null=True)
    test_procedure = CKEditor5Field('Test Procedure', config_name='extends', blank=True, null=True)
    test_results = CKEditor5Field('Test Results', config_name='extends', blank=True, null=True)
    test_result = models.CharField(max_length=20, choices=TEST_RESULT_CHOICES)
    exceptions_found = models.BooleanField(default=False)
    exception_details = CKEditor5Field('Exception Details', config_name='extends', blank=True, null=True)
    remediation_required = models.BooleanField(default=False)
    remediation_plan = CKEditor5Field('Remediation Plan', config_name='extends', blank=True, null=True)
    remediation_due_date = models.DateField(null=True, blank=True)
    
    class Meta:
        verbose_name = "Financial Control Test"
        verbose_name_plural = "Financial Control Tests"
        constraints = [
            models.CheckConstraint(
                check=models.Q(organization__isnull=False),
                name='organization_required_financialcontroltest'
            )
        ]

class SegregationOfDuties(OrganizationOwnedModel, AuditableModel):
    """
    SOX Segregation of Duties Matrix
    """
    VIOLATION_TYPE_CHOICES = [
        ('authorization_execution', 'Authorization and Execution'),
        ('authorization_custody', 'Authorization and Custody'),
        ('authorization_recording', 'Authorization and Recording'),
        ('execution_custody', 'Execution and Custody'),
        ('execution_recording', 'Execution and Recording'),
        ('custody_recording', 'Custody and Recording'),
    ]
    
    SEVERITY_CHOICES = [
        ('low', 'Low Risk'),
        ('medium', 'Medium Risk'),
        ('high', 'High Risk'),
        ('critical', 'Critical Risk'),
    ]
    
    user = models.ForeignKey(get_user_model(), on_delete=models.CASCADE)
    conflicting_role = models.CharField(max_length=255)
    violation_type = models.CharField(max_length=30, choices=VIOLATION_TYPE_CHOICES)
    severity = models.CharField(max_length=20, choices=SEVERITY_CHOICES)
    description = CKEditor5Field('Description', config_name='extends', blank=True, null=True)
    mitigation_controls = CKEditor5Field('Mitigation Controls', config_name='extends', blank=True, null=True)
    review_frequency = models.CharField(
        max_length=20,
        choices=[
            ('monthly', 'Monthly'),
            ('quarterly', 'Quarterly'),
            ('annually', 'Annually'),
        ],
        default='quarterly'
    )
    last_review_date = models.DateField(null=True, blank=True)
    next_review_date = models.DateField(null=True, blank=True)
    
    class Meta:
        verbose_name = "Segregation of Duties"
        verbose_name_plural = "Segregation of Duties"
        constraints = [
            models.CheckConstraint(
                check=models.Q(organization__isnull=False),
                name='organization_required_segregationofduties'
            )
        ]