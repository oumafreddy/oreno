from rest_framework import serializers
from .models import ContractType, Party, Contract, ContractParty, ContractMilestone

class ContractTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = ContractType
        fields = '__all__'

class PartySerializer(serializers.ModelSerializer):
    class Meta:
        model = Party
        fields = '__all__'

class ContractSerializer(serializers.ModelSerializer):
    class Meta:
        model = Contract
        fields = '__all__'

class ContractPartySerializer(serializers.ModelSerializer):
    class Meta:
        model = ContractParty
        fields = '__all__'

class ContractMilestoneSerializer(serializers.ModelSerializer):
    class Meta:
        model = ContractMilestone
        fields = '__all__' 