from django.conf import settings
from django.db import models

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


class TestResult(OrganizationOwnedModel, AuditableModel, SoftDeletionModel):
    """
    Normalized output per test (e.g., demographic parity, robustness score).
    """
    test_run = models.ForeignKey(TestRun, on_delete=models.CASCADE, related_name='results')
    test_name = models.CharField(max_length=255, db_index=True)
    summary = models.JSONField(default=dict, blank=True)
    passed = models.BooleanField(default=False)

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
