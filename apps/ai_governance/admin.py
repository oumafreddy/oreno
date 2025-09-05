from django.contrib import admin
from django.utils.html import format_html

from .models import (
    ModelAsset,
    DatasetAsset,
    TestPlan,
    TestRun,
    TestResult,
    Metric,
    EvidenceArtifact,
    Framework,
    Clause,
    ComplianceMapping,
    ConnectorConfig,
    WebhookSubscription,
)


@admin.register(ModelAsset)
class ModelAssetAdmin(admin.ModelAdmin):
    list_display = ('name', 'organization', 'model_type', 'version', 'contains_pii', 'data_classification', 'created_at')
    list_filter = ('organization', 'model_type', 'contains_pii', 'data_classification')
    search_fields = ('name', 'uri', 'version')
    ordering = ('-created_at',)
    readonly_fields = ('created_at', 'updated_at', 'created_by', 'updated_by')
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'model_type', 'uri', 'version')
        }),
        ('Model Details', {
            'fields': ('signature', 'extra')
        }),
        ('Security & Privacy', {
            'fields': ('contains_pii', 'data_classification', 'encryption_key_id'),
            'classes': ('collapse',)
        }),
        ('Audit Information', {
            'fields': ('created_at', 'updated_at', 'created_by', 'updated_by'),
            'classes': ('collapse',)
        }),
    )

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('organization', 'created_by', 'updated_by')


@admin.register(DatasetAsset)
class DatasetAssetAdmin(admin.ModelAdmin):
    list_display = ('name', 'organization', 'role', 'format', 'contains_pii', 'data_classification', 'retention_date', 'created_at')
    list_filter = ('organization', 'role', 'format', 'contains_pii', 'data_classification')
    search_fields = ('name', 'path', 'label')
    ordering = ('-created_at',)
    readonly_fields = ('created_at', 'updated_at', 'created_by', 'updated_by')
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'role', 'path', 'format', 'label')
        }),
        ('Dataset Details', {
            'fields': ('schema', 'sensitive_attributes', 'extra')
        }),
        ('Security & Privacy', {
            'fields': ('contains_pii', 'data_classification', 'encryption_key_id', 'retention_date'),
            'classes': ('collapse',)
        }),
        ('Audit Information', {
            'fields': ('created_at', 'updated_at', 'created_by', 'updated_by'),
            'classes': ('collapse',)
        }),
    )

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('organization', 'created_by', 'updated_by')


@admin.register(TestPlan)
class TestPlanAdmin(admin.ModelAdmin):
    list_display = ('name', 'organization', 'model_type', 'created_at')
    list_filter = ('organization', 'model_type')
    search_fields = ('name',)
    ordering = ('-created_at',)
    readonly_fields = ('created_at', 'updated_at', 'created_by', 'updated_by')
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'model_type')
        }),
        ('Configuration', {
            'fields': ('config', 'alert_rules')
        }),
        ('Audit Information', {
            'fields': ('created_at', 'updated_at', 'created_by', 'updated_by'),
            'classes': ('collapse',)
        }),
    )

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('organization', 'created_by', 'updated_by')


@admin.register(TestRun)
class TestRunAdmin(admin.ModelAdmin):
    list_display = ('id', 'organization', 'model_asset', 'dataset_asset', 'test_plan', 'status', 'contains_pii', 'data_classification', 'created_at')
    list_filter = ('organization', 'status', 'contains_pii', 'data_classification')
    search_fields = ('id', 'model_asset__name', 'dataset_asset__name')
    ordering = ('-created_at',)
    readonly_fields = ('created_at', 'updated_at', 'created_by', 'updated_by', 'started_at', 'completed_at', 'worker_info')
    
    fieldsets = (
        ('Test Configuration', {
            'fields': ('model_asset', 'dataset_asset', 'test_plan', 'parameters')
        }),
        ('Execution Status', {
            'fields': ('status', 'started_at', 'completed_at', 'error_message', 'worker_info')
        }),
        ('Security & Privacy', {
            'fields': ('contains_pii', 'data_classification', 'encryption_key_id', 'retention_date'),
            'classes': ('collapse',)
        }),
        ('Audit Information', {
            'fields': ('created_at', 'updated_at', 'created_by', 'updated_by'),
            'classes': ('collapse',)
        }),
    )

    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'organization', 'model_asset', 'dataset_asset', 'test_plan', 'created_by', 'updated_by'
        )


@admin.register(TestResult)
class TestResultAdmin(admin.ModelAdmin):
    list_display = ('id', 'organization', 'test_run', 'test_name', 'passed', 'contains_pii', 'data_classification', 'created_at')
    list_filter = ('organization', 'test_name', 'passed', 'contains_pii', 'data_classification')
    search_fields = ('test_name', 'test_run__id')
    ordering = ('-created_at',)
    readonly_fields = ('created_at', 'updated_at', 'created_by', 'updated_by')
    
    fieldsets = (
        ('Test Information', {
            'fields': ('test_run', 'test_name', 'summary', 'passed')
        }),
        ('Security & Privacy', {
            'fields': ('contains_pii', 'data_classification', 'encryption_key_id'),
            'classes': ('collapse',)
        }),
        ('Audit Information', {
            'fields': ('created_at', 'updated_at', 'created_by', 'updated_by'),
            'classes': ('collapse',)
        }),
    )

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('organization', 'test_run', 'created_by', 'updated_by')


@admin.register(Metric)
class MetricAdmin(admin.ModelAdmin):
    list_display = ('id', 'organization', 'test_result', 'name', 'value', 'threshold', 'passed', 'created_at')
    list_filter = ('organization', 'name', 'passed')
    search_fields = ('name', 'test_result__test_name')
    ordering = ('-created_at',)
    readonly_fields = ('created_at', 'updated_at', 'created_by', 'updated_by')
    
    fieldsets = (
        ('Metric Information', {
            'fields': ('test_result', 'name', 'value', 'threshold', 'passed', 'slice_key', 'slice_value', 'extra')
        }),
        ('Audit Information', {
            'fields': ('created_at', 'updated_at', 'created_by', 'updated_by'),
            'classes': ('collapse',)
        }),
    )

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('organization', 'test_result', 'created_by', 'updated_by')


@admin.register(EvidenceArtifact)
class EvidenceArtifactAdmin(admin.ModelAdmin):
    list_display = ('id', 'organization', 'test_run', 'artifact_type', 'file_path', 'contains_pii', 'data_classification', 'retention_date', 'created_at')
    list_filter = ('organization', 'artifact_type', 'contains_pii', 'data_classification')
    search_fields = ('file_path', 'test_run__id')
    ordering = ('-created_at',)
    readonly_fields = ('created_at', 'updated_at', 'created_by', 'updated_by')
    
    fieldsets = (
        ('Artifact Information', {
            'fields': ('test_run', 'artifact_type', 'file_path', 'file_info')
        }),
        ('Security & Privacy', {
            'fields': ('contains_pii', 'data_classification', 'encryption_key_id', 'retention_date'),
            'classes': ('collapse',)
        }),
        ('Audit Information', {
            'fields': ('created_at', 'updated_at', 'created_by', 'updated_by'),
            'classes': ('collapse',)
        }),
    )

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('organization', 'test_run', 'created_by', 'updated_by')


@admin.register(Framework)
class FrameworkAdmin(admin.ModelAdmin):
    list_display = ('code', 'title', 'version', 'organization', 'created_at')
    list_filter = ('organization', 'code', 'version')
    search_fields = ('code', 'title')
    ordering = ('-created_at',)
    readonly_fields = ('created_at', 'updated_at', 'created_by', 'updated_by')
    
    fieldsets = (
        ('Framework Information', {
            'fields': ('code', 'title', 'version', 'metadata')
        }),
        ('Audit Information', {
            'fields': ('created_at', 'updated_at', 'created_by', 'updated_by'),
            'classes': ('collapse',)
        }),
    )

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('organization', 'created_by', 'updated_by')


@admin.register(Clause)
class ClauseAdmin(admin.ModelAdmin):
    list_display = ('framework', 'clause_code', 'organization', 'created_at')
    list_filter = ('organization', 'framework')
    search_fields = ('clause_code', 'framework__code', 'text')
    ordering = ('-created_at',)
    readonly_fields = ('created_at', 'updated_at', 'created_by', 'updated_by')
    
    fieldsets = (
        ('Clause Information', {
            'fields': ('framework', 'clause_code', 'text', 'metadata')
        }),
        ('Audit Information', {
            'fields': ('created_at', 'updated_at', 'created_by', 'updated_by'),
            'classes': ('collapse',)
        }),
    )

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('organization', 'framework', 'created_by', 'updated_by')


@admin.register(ComplianceMapping)
class ComplianceMappingAdmin(admin.ModelAdmin):
    list_display = ('test_name', 'metric_name', 'clause', 'organization', 'created_at')
    list_filter = ('organization', 'clause__framework')
    search_fields = ('test_name', 'metric_name', 'clause__clause_code')
    ordering = ('-created_at',)
    readonly_fields = ('created_at', 'updated_at', 'created_by', 'updated_by')
    
    fieldsets = (
        ('Mapping Information', {
            'fields': ('test_name', 'metric_name', 'clause', 'rationale', 'evidence_rule')
        }),
        ('Audit Information', {
            'fields': ('created_at', 'updated_at', 'created_by', 'updated_by'),
            'classes': ('collapse',)
        }),
    )

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('organization', 'clause', 'created_by', 'updated_by')


@admin.register(ConnectorConfig)
class ConnectorConfigAdmin(admin.ModelAdmin):
    list_display = ('name', 'connector_type', 'organization', 'is_active', 'created_at')
    list_filter = ('organization', 'connector_type', 'is_active')
    search_fields = ('name',)
    ordering = ('-created_at',)
    readonly_fields = ('created_at', 'updated_at', 'created_by', 'updated_by')
    
    fieldsets = (
        ('Connector Information', {
            'fields': ('connector_type', 'name', 'config', 'is_active')
        }),
        ('Audit Information', {
            'fields': ('created_at', 'updated_at', 'created_by', 'updated_by'),
            'classes': ('collapse',)
        }),
    )

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('organization', 'created_by', 'updated_by')


@admin.register(WebhookSubscription)
class WebhookSubscriptionAdmin(admin.ModelAdmin):
    list_display = ('url', 'organization', 'events_display', 'is_active', 'created_at')
    list_filter = ('organization', 'is_active')
    search_fields = ('url',)
    ordering = ('-created_at',)
    readonly_fields = ('created_at', 'updated_at', 'created_by', 'updated_by')
    
    fieldsets = (
        ('Webhook Information', {
            'fields': ('url', 'events', 'secret', 'is_active')
        }),
        ('Audit Information', {
            'fields': ('created_at', 'updated_at', 'created_by', 'updated_by'),
            'classes': ('collapse',)
        }),
    )

    def events_display(self, obj):
        """Display events as a comma-separated list."""
        if obj.events:
            return ', '.join(obj.events)
        return '-'
    events_display.short_description = 'Events'

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('organization', 'created_by', 'updated_by')
