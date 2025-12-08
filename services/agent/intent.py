from rest_framework import serializers


class IntentSerializer(serializers.Serializer):
    action = serializers.ChoiceField(choices=["create", "update", "delete", "read", "generate_report"])
    model = serializers.CharField()
    fields = serializers.DictField(child=serializers.JSONField(), required=False)
    filters = serializers.DictField(child=serializers.JSONField(), required=False)
    id = serializers.IntegerField(required=False)
    preview = serializers.BooleanField(required=False, default=False)
