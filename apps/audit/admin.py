# apps/audit/admin.py

from django.contrib import admin
from django.contrib.contenttypes.admin import GenericTabularInline
from django.utils.translation import gettext_lazy as _
import reversion.admin

from .models.workplan import AuditWorkplan
from .models.engagement import Engagement
from .models.issue import Issue
from .models.approval import Approval


class ApprovalInline(GenericTabularInline):
    """
    Inline display of Approval entries for any approved model,
    using GenericForeignKey (content_type + object_id).
    """
    model = Approval
    # tell it which fields represent the relation
    content_type_field = "content_type"
    object_id_field    = "object_id"

    readonly_fields = (
        "content_type", "object_id",
        "requester", "approver",
        "status", "comments",
        "created_at", "updated_at",
    )
    extra      = 0
    can_delete = False


@admin.register(AuditWorkplan)
class AuditWorkplanAdmin(reversion.admin.VersionAdmin):
    list_display   = ("code", "name", "organization", "fiscal_year", "state", "creation_date")
    list_filter    = ("organization", "fiscal_year", "state")
    search_fields  = ("code", "name")
    inlines        = [ApprovalInline]
    date_hierarchy = "creation_date"
    
    # Make state field read-only in the admin form
    readonly_fields = ("state",)
    
    # Add state transition actions
    actions = ['submit_for_approval', 'approve', 'reject']
    
    def submit_for_approval(self, request, queryset):
        for workplan in queryset:
            if workplan.state == 'draft':
                workplan.submit_for_approval()
                workplan.save()
    submit_for_approval.short_description = "Submit selected workplans for approval"
    
    def approve(self, request, queryset):
        for workplan in queryset:
            if workplan.state == 'pending':
                workplan.approve()
                workplan.save()
    approve.short_description = "Approve selected workplans"
    
    def reject(self, request, queryset):
        for workplan in queryset:
            if workplan.state == 'pending':
                workplan.reject()
                workplan.save()
    reject.short_description = "Reject selected workplans"
    
    def get_actions(self, request):
        actions = super().get_actions(request)
        if not request.user.has_perm('audit.can_approve_workplan'):
            if 'approve' in actions:
                del actions['approve']
            if 'reject' in actions:
                del actions['reject']
        return actions


@admin.register(Engagement)
class EngagementAdmin(reversion.admin.VersionAdmin):
    list_display   = (
        "code", "title", "audit_workplan", "organization",
        "project_status", "assigned_to", "assigned_by",
        "project_start_date", "target_end_date", "state",
    )
    list_filter    = ("organization", "project_status", "state")
    search_fields  = ("code", "title", "audit_workplan__code")
    inlines        = [ApprovalInline]
    date_hierarchy = "project_start_date"
    
    # Make state field read-only in the admin form
    readonly_fields = ("state",)
    
    # Add state transition actions
    actions = ['submit_for_approval', 'approve', 'reject']
    
    def submit_for_approval(self, request, queryset):
        for engagement in queryset:
            if engagement.state == 'draft':
                engagement.submit_for_approval()
                engagement.save()
    submit_for_approval.short_description = "Submit selected engagements for approval"
    
    def approve(self, request, queryset):
        for engagement in queryset:
            if engagement.state == 'pending':
                engagement.approve()
                engagement.save()
    approve.short_description = "Approve selected engagements"
    
    def reject(self, request, queryset):
        for engagement in queryset:
            if engagement.state == 'pending':
                engagement.reject()
                engagement.save()
    reject.short_description = "Reject selected engagements"
    
    def get_actions(self, request):
        actions = super().get_actions(request)
        if not request.user.has_perm('audit.can_approve_engagement'):
            if 'approve' in actions:
                del actions['approve']
            if 'reject' in actions:
                del actions['reject']
        return actions


@admin.register(Issue)
class IssueAdmin(reversion.admin.VersionAdmin):
    list_display   = (
        "code", "issue_title", "organization", "engagement",
        "issue_status", "severity_status", "date_identified",
    )
    list_filter    = ("organization", "issue_status", "severity_status")
    search_fields  = ("code", "issue_title", "engagement__code")
    inlines        = [ApprovalInline]
    date_hierarchy = "date_identified"


@admin.register(Approval)
class ApprovalAdmin(admin.ModelAdmin):
    list_display   = (
        "content_object", "organization",
        "requester", "approver", "status", "created_at",
    )
    list_filter    = ("organization", "status")
    search_fields  = (
        "content_type__model", "object_id",
        "requester__email", "approver__email",
    )
    date_hierarchy = "created_at"
