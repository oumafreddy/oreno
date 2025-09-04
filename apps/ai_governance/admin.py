from django.contrib import admin

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
    list_display = ('name', 'organization', 'model_type', 'version', 'created_at')
    list_filter = ('organization', 'model_type')
    search_fields = ('name', 'uri')
    ordering = ('-created_at',)


@admin.register(DatasetAsset)
class DatasetAssetAdmin(admin.ModelAdmin):
    list_display = ('name', 'organization', 'role', 'format', 'created_at')
    list_filter = ('organization', 'role', 'format')
    search_fields = ('name', 'path')
    ordering = ('-created_at',)


@admin.register(TestPlan)
class TestPlanAdmin(admin.ModelAdmin):
    list_display = ('name', 'organization', 'model_type', 'created_at')
    list_filter = ('organization', 'model_type')
    search_fields = ('name',)
    ordering = ('-created_at',)


@admin.register(TestRun)
class TestRunAdmin(admin.ModelAdmin):
    list_display = ('id', 'organization', 'model_asset', 'dataset_asset', 'test_plan', 'status', 'created_at')
    list_filter = ('organization', 'status')
    search_fields = ('id', 'model_asset__name')
    ordering = ('-created_at',)


@admin.register(TestResult)
class TestResultAdmin(admin.ModelAdmin):
    list_display = ('id', 'organization', 'test_run', 'test_name', 'passed', 'created_at')
    list_filter = ('organization', 'test_name', 'passed')
    search_fields = ('test_name',)
    ordering = ('-created_at',)


@admin.register(Metric)
class MetricAdmin(admin.ModelAdmin):
    list_display = ('id', 'organization', 'test_result', 'name', 'value', 'passed', 'created_at')
    list_filter = ('organization', 'name', 'passed')
    search_fields = ('name',)
    ordering = ('-created_at',)


@admin.register(EvidenceArtifact)
class EvidenceArtifactAdmin(admin.ModelAdmin):
    list_display = ('id', 'organization', 'test_run', 'artifact_type', 'file_path', 'created_at')
    list_filter = ('organization', 'artifact_type')
    search_fields = ('file_path',)
    ordering = ('-created_at',)


@admin.register(Framework)
class FrameworkAdmin(admin.ModelAdmin):
    list_display = ('code', 'title', 'version', 'organization', 'created_at')
    list_filter = ('organization', 'code', 'version')
    search_fields = ('code', 'title')
    ordering = ('-created_at',)


@admin.register(Clause)
class ClauseAdmin(admin.ModelAdmin):
    list_display = ('framework', 'clause_code', 'organization', 'created_at')
    list_filter = ('organization', 'framework')
    search_fields = ('clause_code', 'framework__code')
    ordering = ('-created_at',)


@admin.register(ComplianceMapping)
class ComplianceMappingAdmin(admin.ModelAdmin):
    list_display = ('test_name', 'metric_name', 'clause', 'organization', 'created_at')
    list_filter = ('organization',)
    search_fields = ('test_name', 'metric_name')
    ordering = ('-created_at',)


@admin.register(ConnectorConfig)
class ConnectorConfigAdmin(admin.ModelAdmin):
    list_display = ('name', 'connector_type', 'organization', 'is_active', 'created_at')
    list_filter = ('organization', 'connector_type', 'is_active')
    search_fields = ('name',)
    ordering = ('-created_at',)


@admin.register(WebhookSubscription)
class WebhookSubscriptionAdmin(admin.ModelAdmin):
    list_display = ('url', 'organization', 'is_active', 'created_at')
    list_filter = ('organization', 'is_active')
    search_fields = ('url',)
    ordering = ('-created_at',)
