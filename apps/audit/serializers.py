# audits/serializers.py

from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.utils.translation import gettext_lazy as _
from .models import (
    AuditWorkplan, Engagement, Recommendation, Issue, IssueWorkingPaper, Objective,
    Procedure, Approval, Note, Risk, Notification, IssueRetest, FollowUpAction
)
from users.serializers import UserSerializer
from users.models import CustomUser

# Forward declaration to handle circular imports
ProcedureSerializer = None

# ─── BASE SERIALIZER ──────────────────────────────────────────────────────────
class BaseAuditSerializer(serializers.ModelSerializer):
    """Base serializer with common functionality for all audit serializers"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Enforce organization filtering for all user-related fields
        request = self.context.get('request', None)
        organization = None
        if request and hasattr(request.user, 'organization') and request.user.organization:
            organization = request.user.organization
        elif request and hasattr(request.user, 'active_organization') and request.user.active_organization:
            organization = request.user.active_organization
        if organization:
            for field_name, field in self.fields.items():
                if hasattr(field, 'queryset') and field.queryset is not None:
                    model = getattr(field.queryset, 'model', None)
                    if model and model.__name__ in ['CustomUser', 'User']:
                        field.queryset = field.queryset.filter(organization=organization)

    def validate_organization(self, value):
        request = self.context.get("request")
        if request and request.user and not request.user.has_audit_access_to_organization(value):
            raise serializers.ValidationError(_("You don't have audit access to this organization"))
        return value
        
    def validate(self, attrs):
        # Ensure organization consistency across related objects
        request = self.context.get('request')
        organization = attrs.get('organization')
        
        # Set organization from user if not provided
        if not organization and request and request.user:
            attrs['organization'] = getattr(request.user, 'organization', None) or getattr(request.user, 'current_organization', None)
            organization = attrs['organization']
            
        # Check related objects have the same organization
        for field_name, field_value in attrs.items():
            if hasattr(field_value, 'organization') and field_value.organization != organization:
                raise serializers.ValidationError({
                    field_name: _("Related object must belong to the same organization")
                })
                
        return attrs

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
            'scope', 'conclusion_description',
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

# ─── RECOMMENDATION SERIALIZER ──────────────────────────────────────────────
class RecommendationSerializer(BaseAuditSerializer):
    issue = serializers.PrimaryKeyRelatedField(
        queryset=Issue.objects.all()
    )
    assigned_to = serializers.PrimaryKeyRelatedField(
        queryset=CustomUser.objects.all(),
        required=False, 
        allow_null=True
    )
    verified_by = serializers.PrimaryKeyRelatedField(
        queryset=CustomUser.objects.all(),
        required=False,
        allow_null=True
    )
    get_absolute_url = serializers.SerializerMethodField()
    
    class Meta:
        model = Recommendation
        fields = [
            'id', 'issue', 'title', 'description', 'priority',
            'cost_benefit_analysis', 'assigned_to', 'estimated_hours',
            'estimated_cost', 'order', 'implementation_status',
            'target_date', 'revised_date', 'extension_reason',
            'implementation_date', 'verification_date', 'verified_by',
            'management_action_plan', 'effectiveness_evaluation',
            'effectiveness_rating', 'organization', 'created_by',
            'created_at', 'updated_at', 'get_absolute_url'
        ]
        read_only_fields = ['created_by', 'created_at', 'updated_at',
                           'implementation_date', 'verification_date']
    
    def get_get_absolute_url(self, obj):
        return obj.get_absolute_url() if hasattr(obj, 'get_absolute_url') else None
        
    def validate(self, data):
        # Validate that target_date is not in the past for new recommendations
        if 'target_date' in data and data['target_date']:
            from datetime import date
            today = date.today()
            if not self.instance and data['target_date'] < today:
                raise serializers.ValidationError({
                    'target_date': _('Target date cannot be in the past')
                })
        return data

# ─── ISSUE SERIALIZERS ────────────────────────────────────────────────────────
class IssueWorkingPaperSerializer(serializers.ModelSerializer):
    class Meta:
        model = IssueWorkingPaper
        fields = ['id', 'issue', 'file', 'description', 'uploaded_at', 'created_by', 'created_at', 'updated_at']
        read_only_fields = ['uploaded_at', 'created_by', 'created_at', 'updated_at']

class IssueSerializer(BaseAuditSerializer):
    engagement = serializers.PrimaryKeyRelatedField(
        queryset=Engagement.objects.all()
    )
    issue_owner = serializers.PrimaryKeyRelatedField(
        queryset=CustomUser.objects.all(),
        required=False,
        allow_null=True
    )
    recommendations = RecommendationSerializer(many=True, read_only=True)
    working_papers = IssueWorkingPaperSerializer(many=True, read_only=True, source='issueworkingpaper_set')
    get_absolute_url = serializers.SerializerMethodField()
    
    class Meta:
        model = Issue
        fields = [
            'id', 'code', 'issue_title', 'issue_description', 'root_cause',
            'risks', 'date_identified', 'issue_owner', 'issue_owner_title',
            'audit_procedures', 'engagement',
            'risk_level', 'issue_status', 'remediation_status',
            'target_date', 'actual_remediation_date',
            'management_action_plan', 'organization',
            'procedure', 'created_by', 'created_at', 'updated_at', 'recommendations', 'working_papers', 'get_absolute_url'
        ]
        read_only_fields = ['created_by', 'created_at', 'updated_at']
    
    def validate(self, data):
        if data.get('actual_remediation_date') and data.get('target_date'):
            if data['actual_remediation_date'] < data['target_date']:
                raise serializers.ValidationError({
                    'actual_remediation_date': _('Actual remediation date cannot be before the target date')
                })
        return data

    def get_get_absolute_url(self, obj):
        return obj.get_absolute_url()

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

# ─── RISK SERIALIZERS ────────────────────────────────────────────────────────
class RiskSerializer(BaseAuditSerializer):
    objective = serializers.PrimaryKeyRelatedField(
        queryset=Objective.objects.all()
    )
    assigned_to = serializers.PrimaryKeyRelatedField(
        queryset=CustomUser.objects.all(),
        required=False,
        allow_null=True
    )
    get_absolute_url = serializers.SerializerMethodField()
    
    class Meta:
        model = Risk
        fields = [
            'id', 'title', 'description', 'category', 'status',
            'risk_appetite', 'risk_tolerance', 'existing_controls',
            'control_effectiveness', 'mitigation_plan', 'target_date',
            'likelihood', 'impact', 'inherent_risk_score', 'residual_risk_score',
            'assigned_to', 'objective', 'organization', 'order',
            'created_by', 'created_at', 'updated_at', 'get_absolute_url'
        ]
        read_only_fields = ['created_by', 'created_at', 'updated_at', 
                          'inherent_risk_score', 'residual_risk_score']
    
    def get_get_absolute_url(self, obj):
        return obj.get_absolute_url()
    
    def validate(self, data):
        # Validate likelihood and impact values
        if 'likelihood' in data and (data['likelihood'] < 1 or data['likelihood'] > 3):
            raise serializers.ValidationError({
                'likelihood': _('Likelihood must be between 1 and 3')
            })
            
        if 'impact' in data and (data['impact'] < 1 or data['impact'] > 3):
            raise serializers.ValidationError({
                'impact': _('Impact must be between 1 and 3')
            })
            
        if 'control_effectiveness' in data and (data['control_effectiveness'] < 1 or 
                                              data['control_effectiveness'] > 3):
            raise serializers.ValidationError({
                'control_effectiveness': _('Control effectiveness must be between 1 and 3')
            })
        
        return data

class NestedRiskSerializer(RiskSerializer):
    class Meta(RiskSerializer.Meta):
        fields = ['id', 'title', 'category', 'status', 'inherent_risk_score', 'residual_risk_score']

# ─── OBJECTIVE SERIALIZER ─────────────────────────────────────────────────────
class ObjectiveSerializer(BaseAuditSerializer):
    procedures = serializers.SerializerMethodField()
    risks = NestedRiskSerializer(many=True, read_only=True, source='risk_set')
    get_absolute_url = serializers.SerializerMethodField()
    engagement = serializers.PrimaryKeyRelatedField(
        queryset=Engagement.objects.all(),
        required=True
    )
    
    class Meta:
        model = Objective
        fields = [
            'id', 'engagement', 'title', 'description', 'category',
            'status', 'priority', 'order', 'organization', 'procedures',
            'risks', 'created_by', 'created_at', 'updated_at', 'get_absolute_url'
        ]
        read_only_fields = ['created_by', 'created_at', 'updated_at']
        
    def get_get_absolute_url(self, obj):
        return obj.get_absolute_url()

    def get_procedures(self, obj):
        # Return basic data to avoid circular reference
        procedures = obj.procedure_set.all()
        return [{
            'id': p.id,
            'title': p.title,
            'description': getattr(p, 'description', ''),
            'status': getattr(p, 'status', None)
        } for p in procedures]

# ─── NESTED SERIALIZERS ──────────────────────────────────────────────────────
class NestedAuditWorkplanSerializer(AuditWorkplanSerializer):
    class Meta(AuditWorkplanSerializer.Meta):
        fields = ['id', 'code', 'name', 'fiscal_year', 'state']

class NestedEngagementSerializer(EngagementSerializer):
    class Meta(EngagementSerializer.Meta):
        fields = ['id', 'code', 'title', 'project_status', 'state']

class NestedIssueSerializer(IssueSerializer):
    class Meta(IssueSerializer.Meta):
        fields = ['id', 'code', 'issue_title', 'risk_level', 'issue_status']

# ─── DETAIL SERIALIZERS ──────────────────────────────────────────────────────
class AuditWorkplanDetailSerializer(AuditWorkplanSerializer):
    engagements = NestedEngagementSerializer(many=True, read_only=True)
    approvals = ApprovalSerializer(many=True, read_only=True)
    
    class Meta(AuditWorkplanSerializer.Meta):
        fields = AuditWorkplanSerializer.Meta.fields + ['engagements', 'approvals']

class ProcedureSerializer(BaseAuditSerializer):
    get_absolute_url = serializers.SerializerMethodField()
    objective = serializers.PrimaryKeyRelatedField(
        queryset=Objective.objects.all(),
        required=True
    )
    assigned_to = serializers.PrimaryKeyRelatedField(
        queryset=CustomUser.objects.all(),
        required=False,
        allow_null=True
    )
    risk = serializers.PrimaryKeyRelatedField(
        queryset=Risk.objects.all(),
        required=False,
        allow_null=True
    )
    
    class Meta:
        model = Procedure
        fields = [
            'id', 'objective', 'title', 'description', 'procedure_type',
            'priority', 'assigned_to', 'test_steps', 'expected_results', 
            'sample_size', 'sample_selection_method', 'status', 'order',
            'due_date', 'organization', 'created_by', 
            'created_at', 'updated_at', 'get_absolute_url'
        ]
        read_only_fields = ['created_by', 'created_at', 'updated_at']
    
    def get_get_absolute_url(self, obj):
        return obj.get_absolute_url()

class EngagementDetailSerializer(EngagementSerializer):
    audit_workplan = NestedAuditWorkplanSerializer(read_only=True)
    issues = NestedIssueSerializer(many=True, read_only=True)
    approvals = ApprovalSerializer(many=True, read_only=True)
    objectives = ObjectiveSerializer(many=True, read_only=True, source='objectives')
    get_absolute_url = serializers.SerializerMethodField()
    
    class Meta(EngagementSerializer.Meta):
        fields = EngagementSerializer.Meta.fields + ['issues', 'approvals', 'objectives', 'get_absolute_url']

    def get_get_absolute_url(self, obj):
        return obj.get_absolute_url()

class IssueDetailSerializer(IssueSerializer):
    engagement = NestedEngagementSerializer(read_only=True)
    approvals = ApprovalSerializer(many=True, read_only=True)
    
    class Meta(IssueSerializer.Meta):
        fields = IssueSerializer.Meta.fields + ['approvals']

class NotificationSerializer(BaseAuditSerializer):
    user = serializers.PrimaryKeyRelatedField(
        queryset=CustomUser.objects.all(),
        required=True
    )
    note = serializers.PrimaryKeyRelatedField(
        queryset=Note.objects.all(),
        required=False,
        allow_null=True
    )
    
    class Meta:
        model = Notification
        fields = ['id', 'user', 'note', 'message', 'notification_type', 
                  'is_read', 'organization', 'created_at']
        read_only_fields = ['id', 'user', 'note', 'message', 'notification_type', 
                          'created_at', 'organization']

    def get_procedures(self, obj):
        # Return basic data without using ProcedureSerializer to avoid circular reference
        procedures = obj.procedure_set.all()
        return [{
            'id': p.id,
            'title': p.title, 
            'description': getattr(p, 'description', ''),
            'status': getattr(p, 'status', None)
        } for p in procedures]

class NoteSerializer(BaseAuditSerializer):
    notifications = NotificationSerializer(many=True, read_only=True)
    content_type = serializers.PrimaryKeyRelatedField(
        queryset=ContentType.objects.all(),
        required=True
    )
    assigned_to = serializers.PrimaryKeyRelatedField(
        queryset=CustomUser.objects.all(),
        required=False,
        allow_null=True
    )
    cleared_by = serializers.PrimaryKeyRelatedField(
        queryset=CustomUser.objects.all(),
        required=False,
        allow_null=True
    )
    closed_by = serializers.PrimaryKeyRelatedField(
        queryset=CustomUser.objects.all(),
        required=False,
        allow_null=True
    )
    
    class Meta:
        model = Note
        fields = [
            'id', 'content_type', 'object_id', 'content', 'note_type',
            'status', 'priority', 'assigned_to', 'due_date', 'cleared_by',
            'cleared_at', 'closed_by', 'closed_at', 'organization', 
            'created_by', 'updated_by', 'created_at', 'updated_at', 'notifications'
        ]
        read_only_fields = ['created_by', 'updated_by', 'organization', 
                          'cleared_at', 'closed_at', 'notifications']

    def create(self, validated_data):
        request = self.context.get('request')
        if request:
            validated_data['created_by'] = request.user
            validated_data['updated_by'] = request.user
            validated_data['organization'] = getattr(request.user, 'organization', None) or getattr(request.user, 'current_organization', None)
        return super().create(validated_data)

    def update(self, instance, validated_data):
        request = self.context.get('request')
        if request:
            validated_data['updated_by'] = request.user
        return super().update(instance, validated_data)

class IssueRetestSerializer(BaseAuditSerializer):
    issue = serializers.PrimaryKeyRelatedField(
        queryset=Issue.objects.all(),
        required=True
    )
    retested_by = serializers.PrimaryKeyRelatedField(
        queryset=CustomUser.objects.all(),
        required=False,
        allow_null=True
    )
    reviewer = serializers.PrimaryKeyRelatedField(
        queryset=CustomUser.objects.all(),
        required=False,
        allow_null=True
    )
    get_absolute_url = serializers.SerializerMethodField()
    
    class Meta:
        model = IssueRetest
        fields = [
            'id', 'issue', 'scheduled_date', 'retest_date', 'retested_by',
            'result', 'test_approach', 'test_evidence', 'notes',
            'verification_status', 'reviewer', 'review_date', 
            'organization', 'created_by', 'created_at', 'updated_at',
            'get_absolute_url'
        ]
        read_only_fields = ['created_by', 'created_at', 'updated_at',
                         'review_date']
    
    def get_get_absolute_url(self, obj):
        return obj.get_absolute_url() if hasattr(obj, 'get_absolute_url') else None
        
    def validate(self, data):
        # Ensure scheduled_date is not in the past for new retests
        if 'scheduled_date' in data and data['scheduled_date']:
            from datetime import date
            today = date.today()
            if not self.instance and data['scheduled_date'] < today:
                raise serializers.ValidationError({
                    'scheduled_date': _('Scheduled date cannot be in the past')
                })
        return data

class FollowUpActionSerializer(BaseAuditSerializer):
    issue = serializers.PrimaryKeyRelatedField(
        queryset=Issue.objects.all(),
        required=False,
        allow_null=True
    )
    recommendation = serializers.PrimaryKeyRelatedField(
        queryset=Recommendation.objects.all(),
        required=False,
        allow_null=True
    )
    assigned_to = serializers.PrimaryKeyRelatedField(
        queryset=CustomUser.objects.all(),
        required=False,
        allow_null=True
    )
    completed_by = serializers.PrimaryKeyRelatedField(
        queryset=CustomUser.objects.all(),
        required=False,
        allow_null=True
    )
    get_absolute_url = serializers.SerializerMethodField()
    
    class Meta:
        model = FollowUpAction
        fields = [
            'id', 'issue', 'recommendation', 'title', 'description',
            'priority', 'estimated_hours', 'assigned_to', 'assigned_team',
            'start_date', 'due_date', 'revised_due_date', 'extension_reason',
            'status', 'completed_at', 'completed_by', 'completion_evidence',
            'notes', 'organization', 'created_by', 'created_at', 'updated_at',
            'get_absolute_url'
        ]
        read_only_fields = ['created_by', 'created_at', 'updated_at',
                         'completed_at']
    
    def get_get_absolute_url(self, obj):
        return obj.get_absolute_url() if hasattr(obj, 'get_absolute_url') else None
        
    def validate(self, data):
        # Ensure either issue or recommendation is provided
        if not data.get('issue') and not data.get('recommendation') and not self.instance:
            raise serializers.ValidationError({
                'non_field_errors': _('Either issue or recommendation must be provided')
            })
            
        # Ensure due_date is not in the past for new actions
        if 'due_date' in data and data['due_date']:
            from datetime import date
            today = date.today()
            if not self.instance and data['due_date'] < today:
                raise serializers.ValidationError({
                    'due_date': _('Due date cannot be in the past')
                })
            
        return data

"""
Detail serializers for the audit app.
These extend the base serializers to provide more detailed information about related objects.
"""

class RecommendationDetailSerializer(RecommendationSerializer):
    issue = IssueSerializer(read_only=True)
    assigned_to = UserSerializer(read_only=True)
    verified_by = UserSerializer(read_only=True)
    created_by = UserSerializer(read_only=True)
    approvals = ApprovalSerializer(many=True, read_only=True)
    followup_actions = serializers.SerializerMethodField()
    
    class Meta(RecommendationSerializer.Meta):
        fields = RecommendationSerializer.Meta.fields + ['approvals', 'followup_actions']
        
    def get_followup_actions(self, obj):
        actions = FollowUpAction.objects.filter(recommendation=obj)
        return FollowUpActionSerializer(actions, many=True, read_only=True).data


class IssueRetestDetailSerializer(IssueRetestSerializer):
    issue = IssueSerializer(read_only=True)
    retested_by = UserSerializer(read_only=True)
    reviewer = UserSerializer(read_only=True)
    created_by = UserSerializer(read_only=True)
    approvals = ApprovalSerializer(many=True, read_only=True)
    
    class Meta(IssueRetestSerializer.Meta):
        fields = IssueRetestSerializer.Meta.fields + ['approvals']


class FollowUpActionDetailSerializer(FollowUpActionSerializer):
    issue = IssueSerializer(read_only=True)
    recommendation = RecommendationSerializer(read_only=True)
    assigned_to = UserSerializer(read_only=True)
    completed_by = UserSerializer(read_only=True)
    created_by = UserSerializer(read_only=True)
    approvals = ApprovalSerializer(many=True, read_only=True)
    
    class Meta(FollowUpActionSerializer.Meta):
        fields = FollowUpActionSerializer.Meta.fields + ['approvals']


class ObjectiveDetailSerializer(ObjectiveSerializer):
    engagement = EngagementSerializer(read_only=True)
    created_by = UserSerializer(read_only=True)
    
    class Meta(ObjectiveSerializer.Meta):
        fields = ObjectiveSerializer.Meta.fields


class RiskDetailSerializer(RiskSerializer):
    created_by = UserSerializer(read_only=True)
    objectives = serializers.SerializerMethodField()
    procedures = serializers.SerializerMethodField()
    issues = serializers.SerializerMethodField()
    approvals = ApprovalSerializer(many=True, read_only=True)
    
    def get_objectives(self, obj):
        """
        Return all related objectives for this risk, maintaining organization-level access control.
        """
        from apps.audit.models import Objective
        
        # Get objectives related to this risk with proper organization filtering
        objectives = Objective.objects.filter(
            risk=obj,
            organization=obj.organization
        ).select_related('engagement', 'created_by')
        
        # Use the ObjectiveSerializer to include all relevant fields
        return ObjectiveSerializer(objectives, many=True, context=self.context).data
    
    def get_procedures(self, obj):
        """
        Return all procedures associated with this risk's objectives,
        maintaining organization-level access control.
        """
        from apps.audit.models import Procedure
        
        # Get objectives related to this risk
        objective_ids = obj.objective_set.values_list('id', flat=True)
        
        # Get all procedures for these objectives with proper organization filtering
        procedures = Procedure.objects.filter(
            objective__in=objective_ids,
            organization=obj.organization
        ).select_related('objective')
        
        # Use the ProcedureSerializer to include all relevant fields
        return ProcedureSerializer(procedures, many=True, context=self.context).data
    
    def get_issues(self, obj):
        """
        Return all issues associated with this risk,
        maintaining organization-level access control.
        """
        from apps.audit.models import Issue
        
        # Get all issues related to this risk with proper organization filtering
        issues = Issue.objects.filter(
            risk=obj,
            organization=obj.organization
        ).select_related('engagement', 'created_by')
        
        # Use the IssueSerializer to include all relevant fields
        return IssueSerializer(issues, many=True, context=self.context).data
    
    class Meta(RiskSerializer.Meta):
        fields = RiskSerializer.Meta.fields + ['objectives', 'procedures', 'issues', 'approvals']
    
    def get_procedures(self, obj):
        procedures = Procedure.objects.filter(objective__in=obj.objective_set.all())
        try:
            from .serializers import ProcedureSerializer
            return ProcedureSerializer(procedures, many=True, read_only=True).data
        except ImportError:
            # Fallback to minimal serialization if there's an import error
            return [{'id': p.id, 'title': p.title} for p in procedures]
        
    def get_objectives(self, obj):
        objectives = obj.objective_set.all()
        try:
            from .serializers import ObjectiveSerializer
            return ObjectiveSerializer(objectives, many=True, read_only=True).data
        except ImportError:
            # Fallback to minimal serialization if there's an import error
            return [{'id': o.id, 'title': o.title} for o in objectives]
    
    def get_issues(self, obj):
        issues = obj.issue_set.all()
        return IssueSerializer(issues, many=True, read_only=True).data
