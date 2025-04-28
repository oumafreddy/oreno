from rest_framework import serializers
from django.utils.translation import gettext_lazy as _
from django.core.cache import cache
from django.db.models import Q

from .models import (
    Organization, OrganizationUser, OrganizationSettings,
    Subscription, Domain, ArchivedOrganization
)

class DomainSerializer(serializers.ModelSerializer):
    class Meta:
        model = Domain
        fields = ['domain', 'is_primary', 'created_at']
        read_only_fields = ['created_at']

class OrganizationSettingsSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrganizationSettings
        fields = ['subscription_plan', 'is_active', 'additional_settings']
        read_only_fields = ['organization']

    def validate_additional_settings(self, value):
        if isinstance(value, str):
            try:
                import json
                json.loads(value)
            except json.JSONDecodeError:
                raise serializers.ValidationError(_("Additional settings must be valid JSON"))
        return value

class SubscriptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Subscription
        fields = ['subscription_plan', 'status', 'start_date', 'end_date', 'auto_renew']
        read_only_fields = ['organization']

    def validate(self, data):
        if data.get('end_date') and data.get('start_date') and data['end_date'] < data['start_date']:
            raise serializers.ValidationError(_("End date cannot be before start date"))
        return data

class OrganizationUserSerializer(serializers.ModelSerializer):
    user_email = serializers.EmailField(source='user.email', read_only=True)
    user_name = serializers.CharField(source='user.get_full_name', read_only=True)

    class Meta:
        model = OrganizationUser
        fields = ['id', 'user', 'user_email', 'user_name', 'role', 'organization']
        read_only_fields = ['organization']

class NestedOrganizationSerializer(serializers.ModelSerializer):
    """Compact organization representation for nested serialization"""
    class Meta:
        model = Organization
        fields = ['id', 'customer_code', 'customer_name']
        read_only_fields = fields

class OrganizationSerializer(serializers.ModelSerializer):
    settings = OrganizationSettingsSerializer(read_only=True)
    subscription = SubscriptionSerializer(read_only=True)
    domains = DomainSerializer(many=True, read_only=True)
    users = OrganizationUserSerializer(source='organizationuser_set', many=True, read_only=True)
    user_count = serializers.SerializerMethodField()
    is_admin = serializers.SerializerMethodField()

    class Meta:
        model = Organization
        fields = [
            'id', 'customer_code', 'customer_name', 'customer_industry',
            'financial_year_end_date', 'description', 'logo', 'is_active',
            'settings', 'subscription', 'domains', 'users', 'user_count',
            'is_admin', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']

    def get_user_count(self, obj):
        cache_key = f'org_{obj.id}_user_count'
        count = cache.get(cache_key)
        if count is None:
            count = obj.organizationuser_set.count()
            cache.set(cache_key, count, 300)  # Cache for 5 minutes
        return count

    def get_is_admin(self, obj):
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return False
        return obj.organizationuser_set.filter(
            user=request.user,
            role__in=['admin', 'manager']
        ).exists()

    def validate_customer_code(self, value):
        if len(value) != 8:
            raise serializers.ValidationError(_("Customer code must be exactly 8 characters"))
        if not value.isalnum():
            raise serializers.ValidationError(_("Customer code must contain only letters and numbers"))
        return value.upper()

    def validate_financial_year_end_date(self, value):
        if value and value.day != 31:
            raise serializers.ValidationError(_("Financial year must end on the 31st of a month"))
        return value

class OrganizationDetailSerializer(OrganizationSerializer):
    """Extended organization serializer with additional fields"""
    recent_activities = serializers.SerializerMethodField()
    audit_stats = serializers.SerializerMethodField()

    class Meta(OrganizationSerializer.Meta):
        fields = OrganizationSerializer.Meta.fields + ['recent_activities', 'audit_stats']

    def get_recent_activities(self, obj):
        from audit.models import AuditWorkplan, Engagement
        from audit.serializers import NestedAuditWorkplanSerializer, NestedEngagementSerializer

        workplans = AuditWorkplan.objects.filter(
            organization=obj
        ).select_related('created_by')[:5]
        
        engagements = Engagement.objects.filter(
            organization=obj
        ).select_related('assigned_to')[:5]

        return {
            'workplans': NestedAuditWorkplanSerializer(workplans, many=True).data,
            'engagements': NestedEngagementSerializer(engagements, many=True).data
        }

    def get_audit_stats(self, obj):
        from audit.models import AuditWorkplan, Engagement, Issue
        from django.db.models import Count

        stats = cache.get(f'org_{obj.id}_audit_stats')
        if stats is None:
            stats = {
                'workplan_count': AuditWorkplan.objects.filter(organization=obj).count(),
                'engagement_count': Engagement.objects.filter(organization=obj).count(),
                'issue_count': Issue.objects.filter(organization=obj).count(),
                'pending_approvals': AuditWorkplan.objects.filter(
                    organization=obj,
                    state='pending'
                ).count()
            }
            cache.set(f'org_{obj.id}_audit_stats', stats, 300)  # Cache for 5 minutes
        return stats

class ArchivedOrganizationSerializer(serializers.ModelSerializer):
    class Meta:
        model = ArchivedOrganization
        fields = [
            'id', 'original_org_id', 'customer_code', 'customer_name',
            'archived_reason', 'archived_by_user', 'was_active',
            'created_at', 'updated_at'
        ]
        read_only_fields = fields