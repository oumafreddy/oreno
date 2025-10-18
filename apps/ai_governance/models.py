from django.conf import settings
from django.db import models
from django.core.exceptions import ValidationError
from django.utils import timezone

from core.models.abstract_models import (
    OrganizationOwnedModel,
    AuditableModel,
    SoftDeletionModel,
)


class ModelAsset(OrganizationOwnedModel, AuditableModel, SoftDeletionModel):
    """
    Registered ML model reference (e.g., MLflow/S3/Azure Blob).
    Tracks URI, type, versioning and optional metadata for governance.
    """
    MODEL_TYPE_CHOICES = [
        ('tabular', 'Tabular'),
        ('image', 'Image'),
        ('generative', 'Generative'),
    ]

    name = models.CharField(max_length=255, db_index=True)
    model_type = models.CharField(max_length=20, choices=MODEL_TYPE_CHOICES)
    uri = models.CharField(max_length=1024, help_text='Registry or storage URI for the model')
    version = models.CharField(max_length=128, blank=True, null=True)
    signature = models.JSONField(default=dict, blank=True)
    extra = models.JSONField(default=dict, blank=True)
    
    # Security fields
    contains_pii = models.BooleanField(default=False, help_text='Whether this model processes PII')
    data_classification = models.CharField(
        max_length=20,
        choices=[
            ('public', 'Public'),
            ('internal', 'Internal'),
            ('confidential', 'Confidential'),
            ('restricted', 'Restricted'),
        ],
        default='internal',
        help_text='Data classification level'
    )
    encryption_key_id = models.CharField(max_length=255, blank=True, null=True, help_text='Encryption key identifier')

    class Meta:
        app_label = 'ai_governance'
        verbose_name = 'Model Asset'
        verbose_name_plural = 'Model Assets'
        indexes = [
            models.Index(fields=['organization']),
            models.Index(fields=['name']),
            models.Index(fields=['model_type']),
        ]

    def __str__(self):
        return f"{self.name} ({self.version or 'latest'})"
    
    def clean(self):
        """Validate model asset data."""
        super().clean()
        
        # Check for PII in model metadata
        from .security import pii_masking_service
        
        # Check signature and extra fields for PII
        text_to_check = []
        if self.signature:
            text_to_check.append(str(self.signature))
        if self.extra:
            text_to_check.append(str(self.extra))
        
        for text in text_to_check:
            detected_pii = pii_masking_service.detect_pii(text)
            if detected_pii:
                self.contains_pii = True
                break
    
    def save(self, *args, **kwargs):
        """Save model asset with security validation."""
        self.clean()
        super().save(*args, **kwargs)


class DatasetAsset(OrganizationOwnedModel, AuditableModel, SoftDeletionModel):
    """
    Registered dataset reference (CSV/Parquet path, schema, and sensitive fields).
    """
    DATA_ROLE_CHOICES = [
        ('train', 'Train'),
        ('validation', 'Validation'),
        ('test', 'Test'),
        ('other', 'Other'),
    ]

    name = models.CharField(max_length=255, db_index=True)
    role = models.CharField(max_length=20, choices=DATA_ROLE_CHOICES, default='test')
    path = models.CharField(max_length=1024, help_text='Storage path/URI to the dataset')
    format = models.CharField(max_length=50, default='parquet', help_text='csv or parquet')
    schema = models.JSONField(default=dict, blank=True)
    sensitive_attributes = models.JSONField(default=list, blank=True)
    label = models.CharField(max_length=128, blank=True, null=True)
    extra = models.JSONField(default=dict, blank=True)
    
    # Security fields
    contains_pii = models.BooleanField(default=False, help_text='Whether this dataset contains PII')
    data_classification = models.CharField(
        max_length=20,
        choices=[
            ('public', 'Public'),
            ('internal', 'Internal'),
            ('confidential', 'Confidential'),
            ('restricted', 'Restricted'),
        ],
        default='internal',
        help_text='Data classification level'
    )
    encryption_key_id = models.CharField(max_length=255, blank=True, null=True, help_text='Encryption key identifier')
    retention_date = models.DateTimeField(blank=True, null=True, help_text='Data retention expiration date')

    class Meta:
        app_label = 'ai_governance'
        verbose_name = 'Dataset Asset'
        verbose_name_plural = 'Dataset Assets'
        indexes = [
            models.Index(fields=['organization']),
            models.Index(fields=['name']),
            models.Index(fields=['role']),
        ]

    def __str__(self):
        return self.name
    
    def clean(self):
        """Validate dataset asset data."""
        super().clean()
        
        # Check for PII in dataset metadata
        from .security import pii_masking_service
        
        # Check schema, sensitive_attributes, and extra fields for PII
        text_to_check = []
        if self.schema:
            text_to_check.append(str(self.schema))
        if self.sensitive_attributes:
            text_to_check.append(str(self.sensitive_attributes))
        if self.extra:
            text_to_check.append(str(self.extra))
        
        for text in text_to_check:
            detected_pii = pii_masking_service.detect_pii(text)
            if detected_pii:
                self.contains_pii = True
                break
    
    def save(self, *args, **kwargs):
        """Save dataset asset with security validation."""
        self.clean()
        super().save(*args, **kwargs)


class TestPlan(OrganizationOwnedModel, AuditableModel, SoftDeletionModel):
    """
    Saved configuration of tests, thresholds and alert rules per model type.
    """
    name = models.CharField(max_length=255, db_index=True)
    model_type = models.CharField(max_length=20, choices=ModelAsset.MODEL_TYPE_CHOICES)
    config = models.JSONField(default=dict, blank=True, help_text='Tests, thresholds, slices')
    alert_rules = models.JSONField(default=dict, blank=True)

    class Meta:
        app_label = 'ai_governance'
        verbose_name = 'Test Plan'
        verbose_name_plural = 'Test Plans'
        unique_together = ('organization', 'name')
        indexes = [
            models.Index(fields=['organization']),
            models.Index(fields=['model_type']),
        ]

    def __str__(self):
        return self.name


class TestRun(OrganizationOwnedModel, AuditableModel, SoftDeletionModel):
    """
    One execution instance (model + dataset + plan + parameters + status + timing).
    """
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('running', 'Running'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
    ]

    model_asset = models.ForeignKey(ModelAsset, on_delete=models.CASCADE, related_name='test_runs')
    dataset_asset = models.ForeignKey(DatasetAsset, on_delete=models.SET_NULL, null=True, blank=True, related_name='test_runs')
    test_plan = models.ForeignKey(TestPlan, on_delete=models.SET_NULL, null=True, blank=True, related_name='test_runs')

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', db_index=True)
    parameters = models.JSONField(default=dict, blank=True)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    error_message = models.TextField(blank=True)
    worker_info = models.JSONField(default=dict, blank=True)
    
    # Security fields
    contains_pii = models.BooleanField(default=False, help_text='Whether this test run processes PII')
    data_classification = models.CharField(
        max_length=20,
        choices=[
            ('public', 'Public'),
            ('internal', 'Internal'),
            ('confidential', 'Confidential'),
            ('restricted', 'Restricted'),
        ],
        default='internal',
        help_text='Data classification level'
    )
    encryption_key_id = models.CharField(max_length=255, blank=True, null=True, help_text='Encryption key identifier')
    retention_date = models.DateTimeField(blank=True, null=True, help_text='Data retention expiration date')

    class Meta:
        app_label = 'ai_governance'
        verbose_name = 'Test Run'
        verbose_name_plural = 'Test Runs'
        indexes = [
            models.Index(fields=['organization']),
            models.Index(fields=['status']),
            models.Index(fields=['created_at']),
        ]

    def __str__(self):
        return f"Run #{self.id} - {self.status}"
    
    def clean(self):
        """Validate test run data."""
        super().clean()
        
        # Check for PII in test run data
        from .security import pii_masking_service
        
        # Check parameters and worker_info for PII
        text_to_check = []
        if self.parameters:
            text_to_check.append(str(self.parameters))
        if self.worker_info:
            text_to_check.append(str(self.worker_info))
        if self.error_message:
            text_to_check.append(self.error_message)
        
        for text in text_to_check:
            detected_pii = pii_masking_service.detect_pii(text)
            if detected_pii:
                self.contains_pii = True
                break
        
        # Inherit data classification from model and dataset
        if self.model_asset:
            self.data_classification = self.model_asset.data_classification
        if self.dataset_asset and self.dataset_asset.data_classification in ['confidential', 'restricted']:
            self.data_classification = self.dataset_asset.data_classification
    
    def save(self, *args, **kwargs):
        """Save test run with security validation."""
        self.clean()
        super().save(*args, **kwargs)


class TestResult(OrganizationOwnedModel, AuditableModel, SoftDeletionModel):
    """
    Normalized output per test (e.g., demographic parity, robustness score).
    """
    test_run = models.ForeignKey(TestRun, on_delete=models.CASCADE, related_name='results')
    test_name = models.CharField(max_length=255, db_index=True)
    summary = models.JSONField(default=dict, blank=True)
    passed = models.BooleanField(default=False)
    
    # Security fields
    contains_pii = models.BooleanField(default=False, help_text='Whether this test result contains PII')
    data_classification = models.CharField(
        max_length=20,
        choices=[
            ('public', 'Public'),
            ('internal', 'Internal'),
            ('confidential', 'Confidential'),
            ('restricted', 'Restricted'),
        ],
        default='internal',
        help_text='Data classification level'
    )
    encryption_key_id = models.CharField(max_length=255, blank=True, null=True, help_text='Encryption key identifier')

    class Meta:
        app_label = 'ai_governance'
        verbose_name = 'Test Result'
        verbose_name_plural = 'Test Results'
        indexes = [
            models.Index(fields=['organization']),
            models.Index(fields=['test_name']),
        ]

    def __str__(self):
        return f"{self.test_name} ({'pass' if self.passed else 'fail'})"
    
    def clean(self):
        """Validate test result data."""
        super().clean()
        
        # Check for PII in test result data
        from .security import pii_masking_service
        
        # Check summary for PII
        if self.summary:
            detected_pii = pii_masking_service.detect_pii(str(self.summary))
            if detected_pii:
                self.contains_pii = True
        
        # Inherit data classification from test run
        if self.test_run:
            self.data_classification = self.test_run.data_classification
    
    def save(self, *args, **kwargs):
        """Save test result with security validation."""
        self.clean()
        super().save(*args, **kwargs)


class Metric(OrganizationOwnedModel, AuditableModel, SoftDeletionModel):
    """
    Atomic metric rows with slice/group context, thresholds and pass/fail.
    """
    test_result = models.ForeignKey(TestResult, on_delete=models.CASCADE, related_name='metrics')
    name = models.CharField(max_length=255, db_index=True)
    value = models.FloatField()
    threshold = models.FloatField(null=True, blank=True)
    passed = models.BooleanField(default=False)
    slice_key = models.CharField(max_length=255, blank=True, null=True)
    slice_value = models.CharField(max_length=255, blank=True, null=True)
    extra = models.JSONField(default=dict, blank=True)

    class Meta:
        app_label = 'ai_governance'
        verbose_name = 'Metric'
        verbose_name_plural = 'Metrics'
        indexes = [
            models.Index(fields=['organization']),
            models.Index(fields=['name']),
        ]

    def __str__(self):
        return f"{self.name}={self.value}"


class EvidenceArtifact(OrganizationOwnedModel, AuditableModel, SoftDeletionModel):
    """
    Paths to generated artifacts (PDFs, raw logs, plots, matrices, SHAP visuals).
    """
    ARTIFACT_TYPE_CHOICES = [
        ('pdf', 'PDF'),
        ('image', 'Image'),
        ('json', 'JSON'),
        ('csv', 'CSV'),
        ('log', 'Log'),
        ('other', 'Other'),
    ]

    test_run = models.ForeignKey(TestRun, on_delete=models.CASCADE, related_name='artifacts')
    artifact_type = models.CharField(max_length=20, choices=ARTIFACT_TYPE_CHOICES, default='other')
    file_path = models.CharField(max_length=1024)
    file_info = models.JSONField(default=dict, blank=True)
    
    # Security fields
    contains_pii = models.BooleanField(default=False, help_text='Whether this artifact contains PII')
    data_classification = models.CharField(
        max_length=20,
        choices=[
            ('public', 'Public'),
            ('internal', 'Internal'),
            ('confidential', 'Confidential'),
            ('restricted', 'Restricted'),
        ],
        default='internal',
        help_text='Data classification level'
    )
    encryption_key_id = models.CharField(max_length=255, blank=True, null=True, help_text='Encryption key identifier')
    retention_date = models.DateTimeField(blank=True, null=True, help_text='Data retention expiration date')

    class Meta:
        app_label = 'ai_governance'
        verbose_name = 'Evidence Artifact'
        verbose_name_plural = 'Evidence Artifacts'
        indexes = [
            models.Index(fields=['organization']),
            models.Index(fields=['artifact_type']),
        ]

    def __str__(self):
        return self.file_path
    
    def clean(self):
        """Validate evidence artifact data."""
        super().clean()
        
        # Check for PII in artifact metadata
        from .security import pii_masking_service
        
        # Check file_info for PII
        if self.file_info:
            detected_pii = pii_masking_service.detect_pii(str(self.file_info))
            if detected_pii:
                self.contains_pii = True
        
        # Inherit data classification from test run
        if self.test_run:
            self.data_classification = self.test_run.data_classification
    
    def save(self, *args, **kwargs):
        """Save evidence artifact with security validation."""
        self.clean()
        super().save(*args, **kwargs)


class Framework(OrganizationOwnedModel, AuditableModel, SoftDeletionModel):
    """
    Registry of governance frameworks (EU AI Act, OECD, NIST AI RMF) with versioning.
    """
    code = models.CharField(max_length=64, db_index=True)
    title = models.CharField(max_length=255)
    version = models.CharField(max_length=64, blank=True, null=True)
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        app_label = 'ai_governance'
        verbose_name = 'Framework'
        verbose_name_plural = 'Frameworks'
        unique_together = ('organization', 'code', 'version')
        indexes = [
            models.Index(fields=['organization']),
            models.Index(fields=['code']),
        ]

    def __str__(self):
        return f"{self.code} {self.version or ''}".strip()


class Clause(OrganizationOwnedModel, AuditableModel, SoftDeletionModel):
    """
    Clause entries for a framework (code, text, version).
    """
    framework = models.ForeignKey(Framework, on_delete=models.CASCADE, related_name='clauses')
    clause_code = models.CharField(max_length=128, db_index=True)
    text = models.TextField()
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        app_label = 'ai_governance'
        verbose_name = 'Clause'
        verbose_name_plural = 'Clauses'
        unique_together = ('framework', 'clause_code')
        indexes = [
            models.Index(fields=['organization']),
            models.Index(fields=['clause_code']),
        ]

    def __str__(self):
        return f"{self.framework.code}:{self.clause_code}"


class ComplianceMapping(OrganizationOwnedModel, AuditableModel, SoftDeletionModel):
    """
    Map a test/metric to framework clause(s) with rationale.
    Data-driven to allow updating without code changes.
    """
    test_name = models.CharField(max_length=255, db_index=True)
    metric_name = models.CharField(max_length=255, blank=True, null=True)
    clause = models.ForeignKey(Clause, on_delete=models.CASCADE, related_name='mappings')
    rationale = models.TextField(blank=True)
    evidence_rule = models.JSONField(default=dict, blank=True)

    class Meta:
        app_label = 'ai_governance'
        verbose_name = 'Compliance Mapping'
        verbose_name_plural = 'Compliance Mappings'
        indexes = [
            models.Index(fields=['organization']),
            models.Index(fields=['test_name']),
            models.Index(fields=['metric_name']),
        ]

    def __str__(self):
        return f"{self.test_name} -> {self.clause}"


class ConnectorConfig(OrganizationOwnedModel, AuditableModel, SoftDeletionModel):
    """
    Per‑org credentials/locations (MLflow, S3/Azure buckets, etc.).
    """
    CONNECTOR_TYPE_CHOICES = [
        ('mlflow', 'MLflow'),
        ('s3', 'S3'),
        ('azure_blob', 'Azure Blob'),
        ('other', 'Other'),
    ]

    connector_type = models.CharField(max_length=32, choices=CONNECTOR_TYPE_CHOICES)
    name = models.CharField(max_length=255, db_index=True)
    config = models.JSONField(default=dict, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        app_label = 'ai_governance'
        verbose_name = 'Connector Config'
        verbose_name_plural = 'Connector Configs'
        unique_together = ('organization', 'name', 'connector_type')
        indexes = [
            models.Index(fields=['organization']),
            models.Index(fields=['connector_type']),
        ]

    def __str__(self):
        return f"{self.name} ({self.connector_type})"


class WebhookSubscription(OrganizationOwnedModel, AuditableModel, SoftDeletionModel):
    """
    Webhook endpoints for CI/CD callbacks and automation.
    """
    EVENT_CHOICES = [
        ('test_run.started', 'test_run.started'),
        ('test_run.completed', 'test_run.completed'),
        ('test_run.failed', 'test_run.failed'),
        ('thresholds.breached', 'thresholds.breached'),
        ('evidence.published', 'evidence.published'),
    ]

    url = models.URLField()
    events = models.JSONField(default=list, blank=True, help_text='List of event names')
    secret = models.CharField(max_length=255, blank=True, null=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        app_label = 'ai_governance'
        verbose_name = 'Webhook Subscription'
        verbose_name_plural = 'Webhook Subscriptions'
        indexes = [
            models.Index(fields=['organization']),
            models.Index(fields=['is_active']),
        ]

    def __str__(self):
        return self.url


class ModelRiskAssessment(OrganizationOwnedModel, AuditableModel, SoftDeletionModel):
    """
    Formal risk assessment for AI/ML models with approval workflow.
    Required before production deployment in regulated environments.
    """
    RISK_LEVEL_CHOICES = [
        ('minimal', 'Minimal Risk'),
        ('limited', 'Limited Risk'),
        ('high', 'High Risk'),
        ('unacceptable', 'Unacceptable Risk'),
    ]
    
    APPROVAL_STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('under_review', 'Under Review'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('requires_changes', 'Requires Changes'),
    ]
    
    model_asset = models.ForeignKey(
        ModelAsset, 
        on_delete=models.CASCADE, 
        related_name='risk_assessments'
    )
    risk_level = models.CharField(
        max_length=20, 
        choices=RISK_LEVEL_CHOICES,
        help_text='Assessed risk level based on model characteristics'
    )
    assessment_date = models.DateTimeField(
        default=timezone.now,
        help_text='Date when risk assessment was conducted'
    )
    assessor = models.ForeignKey(
        'users.CustomUser',
        on_delete=models.PROTECT,
        related_name='conducted_assessments',
        help_text='User who conducted the risk assessment'
    )
    approval_status = models.CharField(
        max_length=20,
        choices=APPROVAL_STATUS_CHOICES,
        default='draft',
        help_text='Current approval status in the workflow'
    )
    approver = models.ForeignKey(
        'users.CustomUser',
        on_delete=models.PROTECT,
        related_name='approved_assessments',
        null=True,
        blank=True,
        help_text='User who approved/rejected the assessment'
    )
    approval_date = models.DateTimeField(
        null=True,
        blank=True,
        help_text='Date when approval/rejection was given'
    )
    approval_notes = models.TextField(
        blank=True,
        help_text='Notes from the approver'
    )
    
    # Risk Assessment Details
    risk_factors = models.JSONField(
        default=dict,
        help_text='Detailed risk factors and their scores'
    )
    mitigation_measures = models.JSONField(
        default=dict,
        help_text='Risk mitigation measures and controls'
    )
    compliance_requirements = models.JSONField(
        default=dict,
        help_text='Applicable compliance requirements'
    )
    evidence_documents = models.JSONField(
        default=list,
        help_text='References to evidence documents and artifacts'
    )
    
    # Production Deployment Controls
    production_approved = models.BooleanField(
        default=False,
        help_text='Whether model is approved for production deployment'
    )
    production_deployment_date = models.DateTimeField(
        null=True,
        blank=True,
        help_text='Date when model was deployed to production'
    )
    deployment_conditions = models.JSONField(
        default=dict,
        help_text='Conditions and restrictions for production deployment'
    )
    
    # Review and Monitoring
    next_review_date = models.DateTimeField(
        null=True,
        blank=True,
        help_text='Date for next risk assessment review'
    )
    review_frequency_months = models.IntegerField(
        default=12,
        help_text='Frequency of risk assessment reviews in months'
    )
    
    class Meta:
        app_label = 'ai_governance'
        verbose_name = 'Model Risk Assessment'
        verbose_name_plural = 'Model Risk Assessments'
        unique_together = ('organization', 'model_asset', 'assessment_date')
        indexes = [
            models.Index(fields=['organization']),
            models.Index(fields=['model_asset']),
            models.Index(fields=['risk_level']),
            models.Index(fields=['approval_status']),
            models.Index(fields=['production_approved']),
        ]

    def __str__(self):
        return f"Risk Assessment: {self.model_asset.name} ({self.risk_level})"
    
    def clean(self):
        """Validate risk assessment data."""
        if self.approval_status in ['approved', 'rejected'] and not self.approver:
            raise ValidationError("Approver must be specified for approved/rejected assessments")
        
        if self.approval_status in ['approved', 'rejected'] and not self.approval_date:
            raise ValidationError("Approval date must be specified for approved/rejected assessments")
        
        if self.production_approved and self.approval_status != 'approved':
            raise ValidationError("Model cannot be approved for production without risk assessment approval")
    
    def can_deploy_to_production(self):
        """Check if model can be deployed to production."""
        return (
            self.approval_status == 'approved' and
            self.production_approved and
            self.risk_level != 'unacceptable'
        )
    
    def get_risk_score(self):
        """Calculate overall risk score based on risk factors."""
        if not self.risk_factors:
            return 0
        
        total_score = 0
        factor_count = 0
        
        for factor, details in self.risk_factors.items():
            if isinstance(details, dict) and 'score' in details:
                total_score += details['score']
                factor_count += 1
        
        return total_score / factor_count if factor_count > 0 else 0
    
    def requires_immediate_review(self):
        """Check if assessment requires immediate review."""
        if not self.next_review_date:
            return False
        
        return timezone.now() >= self.next_review_date
    
    def save(self, *args, **kwargs):
        """Override save to set next review date."""
        if not self.next_review_date and self.approval_status == 'approved':
            from datetime import timedelta
            self.next_review_date = timezone.now() + timedelta(days=30 * self.review_frequency_months)
        
        self.clean()
        super().save(*args, **kwargs)
