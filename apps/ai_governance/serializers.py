from rest_framework import serializers
from django.utils import timezone

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


class ModelAssetSerializer(serializers.ModelSerializer):
    """Serializer for ModelAsset with security field handling."""
    
    # Read-only fields for audit information
    created_at = serializers.DateTimeField(read_only=True)
    updated_at = serializers.DateTimeField(read_only=True)
    created_by = serializers.StringRelatedField(read_only=True)
    updated_by = serializers.StringRelatedField(read_only=True)
    
    # Computed fields
    organization_name = serializers.CharField(source='organization.name', read_only=True)
    
    class Meta:
        model = ModelAsset
        fields = [
            'id', 'name', 'model_type', 'uri', 'version', 'signature', 'extra',
            'contains_pii', 'data_classification', 'encryption_key_id',
            'organization', 'organization_name',
            'created_at', 'updated_at', 'created_by', 'updated_by'
        ]
        read_only_fields = ['id', 'organization', 'created_at', 'updated_at', 'created_by', 'updated_by']
    
    def validate(self, data):
        """Validate model asset data and check for PII."""
        # Check for PII in signature and extra fields
        if data.get('signature'):
            from .security import pii_masking_service
            detected_pii = pii_masking_service.detect_pii(str(data['signature']))
            if detected_pii:
                data['contains_pii'] = True
        
        if data.get('extra'):
            from .security import pii_masking_service
            detected_pii = pii_masking_service.detect_pii(str(data['extra']))
            if detected_pii:
                data['contains_pii'] = True
        
        return data


class DatasetAssetSerializer(serializers.ModelSerializer):
    """Serializer for DatasetAsset with security field handling."""
    
    # Read-only fields for audit information
    created_at = serializers.DateTimeField(read_only=True)
    updated_at = serializers.DateTimeField(read_only=True)
    created_by = serializers.StringRelatedField(read_only=True)
    updated_by = serializers.StringRelatedField(read_only=True)
    
    # Computed fields
    organization_name = serializers.CharField(source='organization.name', read_only=True)
    
    class Meta:
        model = DatasetAsset
        fields = [
            'id', 'name', 'role', 'path', 'format', 'schema', 'sensitive_attributes',
            'label', 'extra', 'contains_pii', 'data_classification', 
            'encryption_key_id', 'retention_date',
            'organization', 'organization_name',
            'created_at', 'updated_at', 'created_by', 'updated_by'
        ]
        read_only_fields = ['id', 'organization', 'created_at', 'updated_at', 'created_by', 'updated_by']
    
    def validate(self, data):
        """Validate dataset asset data and check for PII."""
        # Check for PII in schema, sensitive_attributes, and extra fields
        fields_to_check = ['schema', 'sensitive_attributes', 'extra']
        
        for field in fields_to_check:
            if data.get(field):
                from .security import pii_masking_service
                detected_pii = pii_masking_service.detect_pii(str(data[field]))
                if detected_pii:
                    data['contains_pii'] = True
                    break
        
        return data


class TestPlanSerializer(serializers.ModelSerializer):
    """Serializer for TestPlan."""
    
    # Read-only fields for audit information
    created_at = serializers.DateTimeField(read_only=True)
    updated_at = serializers.DateTimeField(read_only=True)
    created_by = serializers.StringRelatedField(read_only=True)
    updated_by = serializers.StringRelatedField(read_only=True)
    
    # Computed fields
    organization_name = serializers.CharField(source='organization.name', read_only=True)
    
    class Meta:
        model = TestPlan
        fields = [
            'id', 'name', 'model_type', 'config', 'alert_rules',
            'organization', 'organization_name',
            'created_at', 'updated_at', 'created_by', 'updated_by'
        ]
        read_only_fields = ['id', 'organization', 'created_at', 'updated_at', 'created_by', 'updated_by']


class TestRunSerializer(serializers.ModelSerializer):
    """Serializer for TestRun with security field handling."""
    
    # Read-only fields for audit information
    created_at = serializers.DateTimeField(read_only=True)
    updated_at = serializers.DateTimeField(read_only=True)
    created_by = serializers.StringRelatedField(read_only=True)
    updated_by = serializers.StringRelatedField(read_only=True)
    
    # Related object information
    model_asset_name = serializers.CharField(source='model_asset.name', read_only=True)
    dataset_asset_name = serializers.CharField(source='dataset_asset.name', read_only=True)
    test_plan_name = serializers.CharField(source='test_plan.name', read_only=True)
    organization_name = serializers.CharField(source='organization.name', read_only=True)
    
    # Computed fields
    execution_time = serializers.SerializerMethodField()
    
    class Meta:
        model = TestRun
        fields = [
            'id', 'model_asset', 'model_asset_name', 'dataset_asset', 'dataset_asset_name',
            'test_plan', 'test_plan_name', 'status', 'parameters', 'started_at', 'completed_at',
            'error_message', 'worker_info', 'contains_pii', 'data_classification',
            'encryption_key_id', 'retention_date', 'organization', 'organization_name',
            'execution_time', 'created_at', 'updated_at', 'created_by', 'updated_by'
        ]
        read_only_fields = [
            'id', 'organization', 'started_at', 'completed_at', 'error_message', 'worker_info',
            'created_at', 'updated_at', 'created_by', 'updated_by'
        ]
    
    def get_execution_time(self, obj):
        """Calculate execution time in seconds."""
        if obj.started_at and obj.completed_at:
            return (obj.completed_at - obj.started_at).total_seconds()
        return None
    
    def validate(self, data):
        """Validate test run data and inherit security settings."""
        # Inherit data classification from model and dataset
        if data.get('model_asset'):
            data['data_classification'] = data['model_asset'].data_classification
            data['contains_pii'] = data['model_asset'].contains_pii
        
        if data.get('dataset_asset') and data['dataset_asset'].data_classification in ['confidential', 'restricted']:
            data['data_classification'] = data['dataset_asset'].data_classification
        
        return data


class TestResultSerializer(serializers.ModelSerializer):
    """Serializer for TestResult with security field handling."""
    
    # Read-only fields for audit information
    created_at = serializers.DateTimeField(read_only=True)
    updated_at = serializers.DateTimeField(read_only=True)
    created_by = serializers.StringRelatedField(read_only=True)
    updated_by = serializers.StringRelatedField(read_only=True)
    
    # Related object information
    test_run_id = serializers.IntegerField(source='test_run.id', read_only=True)
    organization_name = serializers.CharField(source='organization.name', read_only=True)
    
    class Meta:
        model = TestResult
        fields = [
            'id', 'test_run', 'test_run_id', 'test_name', 'summary', 'passed',
            'contains_pii', 'data_classification', 'encryption_key_id',
            'organization', 'organization_name',
            'created_at', 'updated_at', 'created_by', 'updated_by'
        ]
        read_only_fields = ['id', 'organization', 'created_at', 'updated_at', 'created_by', 'updated_by']
    
    def validate(self, data):
        """Validate test result data and inherit security settings."""
        # Inherit data classification from test run
        if data.get('test_run'):
            data['data_classification'] = data['test_run'].data_classification
        
        return data


class MetricSerializer(serializers.ModelSerializer):
    """Serializer for Metric."""
    
    # Read-only fields for audit information
    created_at = serializers.DateTimeField(read_only=True)
    updated_at = serializers.DateTimeField(read_only=True)
    created_by = serializers.StringRelatedField(read_only=True)
    updated_by = serializers.StringRelatedField(read_only=True)
    
    # Related object information
    test_result_id = serializers.IntegerField(source='test_result.id', read_only=True)
    test_name = serializers.CharField(source='test_result.test_name', read_only=True)
    organization_name = serializers.CharField(source='organization.name', read_only=True)
    
    class Meta:
        model = Metric
        fields = [
            'id', 'test_result', 'test_result_id', 'test_name', 'name', 'value',
            'threshold', 'passed', 'slice_key', 'slice_value', 'extra',
            'organization', 'organization_name',
            'created_at', 'updated_at', 'created_by', 'updated_by'
        ]
        read_only_fields = ['id', 'organization', 'created_at', 'updated_at', 'created_by', 'updated_by']


class EvidenceArtifactSerializer(serializers.ModelSerializer):
    """Serializer for EvidenceArtifact with security field handling."""
    
    # Read-only fields for audit information
    created_at = serializers.DateTimeField(read_only=True)
    updated_at = serializers.DateTimeField(read_only=True)
    created_by = serializers.StringRelatedField(read_only=True)
    updated_by = serializers.StringRelatedField(read_only=True)
    
    # Related object information
    test_run_id = serializers.IntegerField(source='test_run.id', read_only=True)
    organization_name = serializers.CharField(source='organization.name', read_only=True)
    
    class Meta:
        model = EvidenceArtifact
        fields = [
            'id', 'test_run', 'test_run_id', 'artifact_type', 'file_path', 'file_info',
            'contains_pii', 'data_classification', 'encryption_key_id', 'retention_date',
            'organization', 'organization_name',
            'created_at', 'updated_at', 'created_by', 'updated_by'
        ]
        read_only_fields = ['id', 'organization', 'created_at', 'updated_at', 'created_by', 'updated_by']
    
    def validate(self, data):
        """Validate evidence artifact data and inherit security settings."""
        # Inherit data classification from test run
        if data.get('test_run'):
            data['data_classification'] = data['test_run'].data_classification
        
        return data


class FrameworkSerializer(serializers.ModelSerializer):
    """Serializer for Framework."""
    
    # Read-only fields for audit information
    created_at = serializers.DateTimeField(read_only=True)
    updated_at = serializers.DateTimeField(read_only=True)
    created_by = serializers.StringRelatedField(read_only=True)
    updated_by = serializers.StringRelatedField(read_only=True)
    
    # Computed fields
    organization_name = serializers.CharField(source='organization.name', read_only=True)
    clause_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Framework
        fields = [
            'id', 'code', 'title', 'version', 'metadata', 'clause_count',
            'organization', 'organization_name',
            'created_at', 'updated_at', 'created_by', 'updated_by'
        ]
        read_only_fields = ['id', 'organization', 'created_at', 'updated_at', 'created_by', 'updated_by']
    
    def get_clause_count(self, obj):
        """Get the number of clauses in this framework."""
        return obj.clauses.count()


class ClauseSerializer(serializers.ModelSerializer):
    """Serializer for Clause."""
    
    # Read-only fields for audit information
    created_at = serializers.DateTimeField(read_only=True)
    updated_at = serializers.DateTimeField(read_only=True)
    created_by = serializers.StringRelatedField(read_only=True)
    updated_by = serializers.StringRelatedField(read_only=True)
    
    # Related object information
    framework_code = serializers.CharField(source='framework.code', read_only=True)
    framework_title = serializers.CharField(source='framework.title', read_only=True)
    organization_name = serializers.CharField(source='organization.name', read_only=True)
    
    class Meta:
        model = Clause
        fields = [
            'id', 'framework', 'framework_code', 'framework_title', 'clause_code',
            'text', 'metadata', 'organization', 'organization_name',
            'created_at', 'updated_at', 'created_by', 'updated_by'
        ]
        read_only_fields = ['id', 'organization', 'created_at', 'updated_at', 'created_by', 'updated_by']


class ComplianceMappingSerializer(serializers.ModelSerializer):
    """Serializer for ComplianceMapping."""
    
    # Read-only fields for audit information
    created_at = serializers.DateTimeField(read_only=True)
    updated_at = serializers.DateTimeField(read_only=True)
    created_by = serializers.StringRelatedField(read_only=True)
    updated_by = serializers.StringRelatedField(read_only=True)
    
    # Related object information
    clause_code = serializers.CharField(source='clause.clause_code', read_only=True)
    framework_code = serializers.CharField(source='clause.framework.code', read_only=True)
    organization_name = serializers.CharField(source='organization.name', read_only=True)
    
    class Meta:
        model = ComplianceMapping
        fields = [
            'id', 'test_name', 'metric_name', 'clause', 'clause_code', 'framework_code',
            'rationale', 'evidence_rule', 'organization', 'organization_name',
            'created_at', 'updated_at', 'created_by', 'updated_by'
        ]
        read_only_fields = ['id', 'organization', 'created_at', 'updated_at', 'created_by', 'updated_by']


class ConnectorConfigSerializer(serializers.ModelSerializer):
    """Serializer for ConnectorConfig."""
    
    # Read-only fields for audit information
    created_at = serializers.DateTimeField(read_only=True)
    updated_at = serializers.DateTimeField(read_only=True)
    created_by = serializers.StringRelatedField(read_only=True)
    updated_by = serializers.StringRelatedField(read_only=True)
    
    # Computed fields
    organization_name = serializers.CharField(source='organization.name', read_only=True)
    
    class Meta:
        model = ConnectorConfig
        fields = [
            'id', 'connector_type', 'name', 'config', 'is_active',
            'organization', 'organization_name',
            'created_at', 'updated_at', 'created_by', 'updated_by'
        ]
        read_only_fields = ['id', 'organization', 'created_at', 'updated_at', 'created_by', 'updated_by']


class WebhookSubscriptionSerializer(serializers.ModelSerializer):
    """Serializer for WebhookSubscription."""
    
    # Read-only fields for audit information
    created_at = serializers.DateTimeField(read_only=True)
    updated_at = serializers.DateTimeField(read_only=True)
    created_by = serializers.StringRelatedField(read_only=True)
    updated_by = serializers.StringRelatedField(read_only=True)
    
    # Computed fields
    organization_name = serializers.CharField(source='organization.name', read_only=True)
    events_display = serializers.SerializerMethodField()
    
    class Meta:
        model = WebhookSubscription
        fields = [
            'id', 'url', 'events', 'events_display', 'secret', 'is_active',
            'organization', 'organization_name',
            'created_at', 'updated_at', 'created_by', 'updated_by'
        ]
        read_only_fields = ['id', 'organization', 'created_at', 'updated_at', 'created_by', 'updated_by']
    
    def get_events_display(self, obj):
        """Display events as a comma-separated list."""
        if obj.events:
            return ', '.join(obj.events)
        return '-'
