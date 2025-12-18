from rest_framework import serializers


class IntentSerializer(serializers.Serializer):
    action = serializers.ChoiceField(choices=["create", "update", "delete", "read", "generate_report", "unknown"])
    model = serializers.CharField(required=False, allow_null=True)
    fields = serializers.DictField(child=serializers.JSONField(), required=False)  # type: ignore[assignment]
    filters = serializers.DictField(child=serializers.JSONField(), required=False)  # type: ignore[assignment]
    id = serializers.IntegerField(required=False)
    preview = serializers.BooleanField(required=False, default=False)
    confidence = serializers.FloatField(required=False, default=0.0)
