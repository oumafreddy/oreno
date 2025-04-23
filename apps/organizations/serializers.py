from rest_framework import serializers
from .models import OrganizationUser, OrganizationSettings

class OrganizationUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrganizationUser
        fields = ['id', 'email', 'role', 'organization']

class OrganizationSettingsSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrganizationSettings
        fields = '__all__'
        read_only_fields = ['organization']