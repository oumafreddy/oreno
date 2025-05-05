from rest_framework import serializers
from .models import (
    ComplianceFramework,
    PolicyDocument,
    DocumentProcessing,
    ComplianceRequirement,
    ComplianceObligation,
    ComplianceEvidence,
)

class ComplianceFrameworkSerializer(serializers.ModelSerializer):
    class Meta:
        model = ComplianceFramework
        fields = '__all__'

class PolicyDocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = PolicyDocument
        fields = '__all__'

class DocumentProcessingSerializer(serializers.ModelSerializer):
    class Meta:
        model = DocumentProcessing
        fields = '__all__'

class ComplianceRequirementSerializer(serializers.ModelSerializer):
    class Meta:
        model = ComplianceRequirement
        fields = '__all__'

class ComplianceObligationSerializer(serializers.ModelSerializer):
    class Meta:
        model = ComplianceObligation
        fields = '__all__'

class ComplianceEvidenceSerializer(serializers.ModelSerializer):
    class Meta:
        model = ComplianceEvidence
        fields = '__all__' 