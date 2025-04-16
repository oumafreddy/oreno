# audits/serializers.py
class ApprovalSerializer(serializers.ModelSerializer):
    def validate_approver(self, value):
        if value.organization != self.context['request'].user.organization:
            raise serializers.ValidationError("Approver must be from same organization")
        if not value.has_perm('audits.approve_annualwork'):
            raise serializers.ValidationError("Approver lacks required permissions")
        return value