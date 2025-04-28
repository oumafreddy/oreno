# audits/serializers.py
from rest_framework import serializers
from django.contrib.contenttypes.models import ContentType
from django.utils.translation import gettext_lazy as _

from organizations.models import Organization
from users.models import CustomUser

from .models import AuditWorkplan, Engagement, Issue, Approval

# ─── BASE SERIALIZER ──────────────────────────────────────────────────────────
class BaseAuditSerializer(serializers.ModelSerializer):
    """Base serializer with common functionality for all audit serializers"""
    
    def validate_organization(self, value):
        request = self.context.get('request')
        if request and not request.user.has_audit_access(value):
            raise serializers.ValidationError(
                _("You don't have permission to access this organization's audit data")
            )
        return value

# ─── WORKPLAN SERIALIZERS ─────────────────────────────────────────────────────
class AuditWorkplanSerializer(BaseAuditSerializer):
    class Meta:
        model = AuditWorkplan
        fields = [
            'id', 'code', 'name', 'fiscal_year', 'objectives',
            'description', 'organization', 'state', 'created_by',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['created_by', 'created_at', 'updated_at']
    
    def validate_fiscal_year(self, value):
        from datetime import date
        current_year = date.today().year
        if value < 2000 or value > current_year + 1:
            raise serializers.ValidationError(
                _('Fiscal year must be between 2000 and %(max_year)s') % 
                {'max_year': current_year + 1}
            )
        return value

# ─── ENGAGEMENT SERIALIZERS ───────────────────────────────────────────────────
class EngagementSerializer(BaseAuditSerializer):
    audit_workplan = serializers.PrimaryKeyRelatedField(
        queryset=AuditWorkplan.objects.all()
    )
    assigned_to = serializers.PrimaryKeyRelatedField(
        queryset=CustomUser.objects.all(),
        required=False,
        allow_null=True
    )
    
    class Meta:
        model = Engagement
        fields = [
            'id', 'code', 'title', 'audit_workplan', 'engagement_type',
            'project_start_date', 'target_end_date', 'assigned_to',
            'assigned_by', 'executive_summary', 'purpose', 'background',
            'scope', 'project_objectives', 'conclusion_description',
            'conclusion', 'project_status', 'organization', 'state',
            'created_by', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_by', 'created_at', 'updated_at']
    
    def validate(self, data):
        if data.get('target_end_date') and data.get('project_start_date'):
            if data['target_end_date'] < data['project_start_date']:
                raise serializers.ValidationError({
                    'target_end_date': _('Target end date must be after project start date')
                })
        return data

# ─── ISSUE SERIALIZERS ────────────────────────────────────────────────────────
class IssueSerializer(BaseAuditSerializer):
    engagement = serializers.PrimaryKeyRelatedField(
        queryset=Engagement.objects.all()
    )
    issue_owner = serializers.PrimaryKeyRelatedField(
        queryset=CustomUser.objects.all(),
        required=False,
        allow_null=True
    )
    
    class Meta:
        model = Issue
        fields = [
            'id', 'code', 'issue_title', 'issue_description', 'root_cause',
            'risks', 'date_identified', 'issue_owner', 'issue_owner_title',
            'audit_procedures', 'recommendation', 'engagement',
            'severity_status', 'issue_status', 'remediation_status',
            'remediation_deadline_date', 'actual_remediation_date',
            'management_action_plan', 'working_papers', 'organization',
            'created_by', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_by', 'created_at', 'updated_at']
    
    def validate(self, data):
        if data.get('actual_remediation_date') and data.get('remediation_deadline_date'):
            if data['actual_remediation_date'] < data['remediation_deadline_date']:
                raise serializers.ValidationError({
                    'actual_remediation_date': _('Actual remediation date cannot be before the deadline')
                })
        return data

# ─── APPROVAL SERIALIZERS ─────────────────────────────────────────────────────
class ApprovalSerializer(BaseAuditSerializer):
    content_type = serializers.PrimaryKeyRelatedField(
        queryset=ContentType.objects.all()
    )
    requester = serializers.PrimaryKeyRelatedField(
        queryset=CustomUser.objects.all()
    )
    approver = serializers.PrimaryKeyRelatedField(
        queryset=CustomUser.objects.all(),
        required=False,
        allow_null=True
    )
    
    class Meta:
        model = Approval
        fields = [
            'id', 'content_type', 'object_id', 'requester', 'approver',
            'status', 'comments', 'organization', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']
    
    def validate_approver(self, value):
        if value and not value.has_perm('audit.can_approve_workplan'):
            raise serializers.ValidationError(
                _("The selected approver doesn't have permission to approve")
            )
        return value
    
    def validate(self, data):
        content_type = data.get('content_type')
        object_id = data.get('object_id')
        
        if content_type and object_id:
            try:
                obj = content_type.get_object_for_this_type(pk=object_id)
                if not obj.organization == self.context['request'].user.current_organization:
                    raise serializers.ValidationError(
                        _("Invalid object for this organization")
                    )
            except Exception:
                raise serializers.ValidationError(_("Invalid object"))
        
        return data

# ─── NESTED SERIALIZERS ──────────────────────────────────────────────────────
class NestedAuditWorkplanSerializer(AuditWorkplanSerializer):
    class Meta(AuditWorkplanSerializer.Meta):
        fields = ['id', 'code', 'name', 'fiscal_year', 'state']

class NestedEngagementSerializer(EngagementSerializer):
    class Meta(EngagementSerializer.Meta):
        fields = ['id', 'code', 'title', 'project_status', 'state']

class NestedIssueSerializer(IssueSerializer):
    class Meta(IssueSerializer.Meta):
        fields = ['id', 'code', 'issue_title', 'severity_status', 'issue_status']

# ─── DETAIL SERIALIZERS ──────────────────────────────────────────────────────
class AuditWorkplanDetailSerializer(AuditWorkplanSerializer):
    engagements = NestedEngagementSerializer(many=True, read_only=True)
    approvals = ApprovalSerializer(many=True, read_only=True)
    
    class Meta(AuditWorkplanSerializer.Meta):
        fields = AuditWorkplanSerializer.Meta.fields + ['engagements', 'approvals']

class EngagementDetailSerializer(EngagementSerializer):
    audit_workplan = NestedAuditWorkplanSerializer(read_only=True)
    issues = NestedIssueSerializer(many=True, read_only=True)
    approvals = ApprovalSerializer(many=True, read_only=True)
    
    class Meta(EngagementSerializer.Meta):
        fields = EngagementSerializer.Meta.fields + ['issues', 'approvals']

class IssueDetailSerializer(IssueSerializer):
    engagement = NestedEngagementSerializer(read_only=True)
    approvals = ApprovalSerializer(many=True, read_only=True)
    
    class Meta(IssueSerializer.Meta):
        fields = IssueSerializer.Meta.fields + ['approvals']