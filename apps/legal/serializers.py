from rest_framework import serializers
from .models import CaseType, LegalParty, LegalCase, CaseParty, LegalTask, LegalDocument, LegalArchive

class CaseTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = CaseType
        fields = '__all__'

class LegalPartySerializer(serializers.ModelSerializer):
    class Meta:
        model = LegalParty
        fields = '__all__'

class LegalCaseSerializer(serializers.ModelSerializer):
    class Meta:
        model = LegalCase
        fields = '__all__'

class CasePartySerializer(serializers.ModelSerializer):
    class Meta:
        model = CaseParty
        fields = '__all__'

class LegalTaskSerializer(serializers.ModelSerializer):
    class Meta:
        model = LegalTask
        fields = '__all__'

class LegalDocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = LegalDocument
        fields = '__all__'

class LegalArchiveSerializer(serializers.ModelSerializer):
    class Meta:
        model = LegalArchive
        fields = '__all__' 