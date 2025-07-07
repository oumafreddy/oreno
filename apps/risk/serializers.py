from rest_framework import serializers
from .models import RiskRegister, RiskMatrixConfig, Risk, Control, KRI, RiskAssessment

class RiskRegisterSerializer(serializers.ModelSerializer):
    class Meta:
        model = RiskRegister
        fields = '__all__'

class RiskMatrixConfigSerializer(serializers.ModelSerializer):
    class Meta:
        model = RiskMatrixConfig
        fields = '__all__'

class RiskSerializer(serializers.ModelSerializer):
    class Meta:
        model = Risk
        fields = '__all__'

class ControlSerializer(serializers.ModelSerializer):
    class Meta:
        model = Control
        fields = '__all__'

class KRISerializer(serializers.ModelSerializer):
    class Meta:
        model = KRI
        fields = '__all__'

class RiskAssessmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = RiskAssessment
        fields = '__all__'

class SummaryCardSerializer(serializers.Serializer):
    total_risks = serializers.IntegerField()
    total_controls = serializers.IntegerField()
    total_kris = serializers.IntegerField()
    total_assessments = serializers.IntegerField()
    high_critical_risks = serializers.IntegerField()
    recent_activity_count = serializers.IntegerField()

class TopRiskSerializer(serializers.ModelSerializer):
    risk_level = serializers.SerializerMethodField()
    class Meta:
        model = Risk
        fields = ['id', 'risk_name', 'risk_owner', 'category', 'status', 'residual_risk_score', 'risk_level']
    def get_risk_level(self, obj):
        return obj.get_risk_level()

class KRIStatusSerializer(serializers.ModelSerializer):
    risk_name = serializers.CharField(source='risk.risk_name')
    status = serializers.SerializerMethodField()
    class Meta:
        model = KRI
        fields = ['id', 'name', 'risk_name', 'status']
    def get_status(self, obj):
        return obj.get_status()

class RecentActivitySerializer(serializers.Serializer):
    message = serializers.CharField()
    timestamp = serializers.DateTimeField()

class AssessmentTimelinePointSerializer(serializers.Serializer):
    date = serializers.DateField()
    avg_score = serializers.FloatField()

class RiskCategoryDistributionSerializer(serializers.Serializer):
    category = serializers.CharField()
    count = serializers.IntegerField()

class RiskStatusDistributionSerializer(serializers.Serializer):
    status = serializers.CharField()
    count = serializers.IntegerField()

class ControlEffectivenessSerializer(serializers.Serializer):
    effectiveness = serializers.CharField()
    count = serializers.IntegerField()

class KRIStatusCountSerializer(serializers.Serializer):
    status = serializers.CharField()
    count = serializers.IntegerField()

class AssessmentTypeCountSerializer(serializers.Serializer):
    assessment_type = serializers.CharField()
    count = serializers.IntegerField() 