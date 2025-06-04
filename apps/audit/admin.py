# apps/audit/admin.py

from django.contrib import admin
from django.contrib.contenttypes.admin import GenericTabularInline
from django.utils.translation import gettext_lazy as _
import reversion.admin
from django.forms.models import BaseInlineFormSet
from django import forms
from django.db.models import Q

from .models.workplan import AuditWorkplan
from .models.engagement import Engagement
from .models.issue import Issue
from .models.approval import Approval
from .models import (
    Objective, Procedure, ProcedureResult, Note
)
from .models.risk import Risk
from .models.followupaction import FollowUpAction
from .models.issueretest import IssueRetest
from .models.recommendation import Recommendation
from .models.note import Notification
from .models.issue_working_paper import IssueWorkingPaper


class OrganizationScopedModelAdmin(admin.ModelAdmin):
    """
    Base ModelAdmin class that enforces organization scoping for all audit app models.
    Ensures that users only see records from their own organization in the admin.
    """
    
    def get_queryset(self, request):
        """
        Override get_queryset to filter by the user's active organization
        """
        queryset = super().get_queryset(request)
        
        # If the user is a superuser, show them everything
        if request.user.is_superuser:
            return queryset
            
        # If user has an active organization, show only records from that organization
        if hasattr(request.user, 'active_organization') and request.user.active_organization:
            return queryset.filter(organization=request.user.active_organization)
            
        # If user belongs to organizations, show records from all their organizations
        if hasattr(request.user, 'organizations'):
            user_orgs = request.user.organizations.all()
            if user_orgs.exists():
                return queryset.filter(organization__in=user_orgs)
                
        return queryset.none()  # Safety: if no organization context, show nothing
    
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        """
        Filter foreign key fields to only show objects from the user's organization
        """
        if db_field.name in ['organization']:
            if hasattr(request.user, 'active_organization') and request.user.active_organization:
                kwargs['queryset'] = db_field.related_model.objects.filter(
                    id=request.user.active_organization.id
                )
            else:
                user_orgs = request.user.organizations.all() if hasattr(request.user, 'organizations') else []
                if user_orgs:
                    kwargs['queryset'] = db_field.related_model.objects.filter(id__in=[org.id for org in user_orgs])
                    
        elif hasattr(db_field.related_model, 'organization'):
            # For any other foreign key to a model that has an organization field
            if hasattr(request.user, 'active_organization') and request.user.active_organization:
                kwargs['queryset'] = db_field.related_model.objects.filter(
                    organization=request.user.active_organization
                )
            else:
                user_orgs = request.user.organizations.all() if hasattr(request.user, 'organizations') else []
                if user_orgs:
                    kwargs['queryset'] = db_field.related_model.objects.filter(organization__in=user_orgs)
                    
        return super().formfield_for_foreignkey(db_field, request, **kwargs)
    
    def save_model(self, request, obj, form, change):
        """
        Ensure that new objects are associated with the user's active organization
        and set audit trail fields
        """
        if not obj.pk and not obj.organization_id and hasattr(request.user, 'active_organization') and request.user.active_organization:
            obj.organization = request.user.active_organization
            
        # Set audit trail fields if they exist on the model
        if hasattr(obj, 'created_by') and not obj.created_by and not change:
            obj.created_by = request.user
        if hasattr(obj, 'updated_by'):
            obj.updated_by = request.user
            
        super().save_model(request, obj, form, change)
    
    def save_formset(self, request, form, formset, change):
        """
        Set organization and audit fields on inline objects
        """
        instances = formset.save(commit=False)
        
        # Set organization and audit fields for all instances
        for instance in instances:
            # If it's new and doesn't have an org set
            if not instance.pk and not getattr(instance, 'organization_id', None):
                # First try to get from parent
                if hasattr(form.instance, 'organization') and form.instance.organization_id:
                    instance.organization = form.instance.organization
                # Otherwise from user's active org
                elif hasattr(request.user, 'active_organization') and request.user.active_organization:
                    instance.organization = request.user.active_organization
            
            # Set audit trail fields if they exist
            if hasattr(instance, 'created_by') and not getattr(instance, 'created_by_id', None):
                instance.created_by = request.user
            if hasattr(instance, 'updated_by'):
                instance.updated_by = request.user
        
        formset.save_m2m()
        super().save_formset(request, form, formset, change)


class OrganizationScopedVersionAdmin(reversion.admin.VersionAdmin, OrganizationScopedModelAdmin):
    """
    Combines reversion's VersionAdmin with our OrganizationScopedModelAdmin
    to provide both versioning and organization scoping
    """
    pass


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


class ProcedureResultInlineFormSet(BaseInlineFormSet):
    def save_new(self, form, commit=True):
        obj = super().save_new(form, commit=False)
        if hasattr(self.instance, 'organization'):
            obj.organization = self.instance.organization
        if commit:
            obj.save()
        return obj


class ProcedureResultInline(admin.TabularInline):
    model = ProcedureResult
    formset = ProcedureResultInlineFormSet
    extra = 1
    fields = ('status', 'notes', 'is_for_the_record', 'order')
    ordering = ('order',)


class ProcedureInlineFormSet(BaseInlineFormSet):
    def save_new(self, form, commit=True):
        obj = super().save_new(form, commit=False)
        if hasattr(self.instance, 'organization'):
            obj.organization = self.instance.organization
        if commit:
            obj.save()
        return obj


class ProcedureInline(admin.TabularInline):
    model = Procedure
    formset = ProcedureInlineFormSet
    extra = 1
    fields = ('title', 'description', 'order')
    ordering = ('order',)
    show_change_link = True


class ObjectiveInlineFormSet(BaseInlineFormSet):
    def save_new(self, form, commit=True):
        obj = super().save_new(form, commit=False)
        if hasattr(self.instance, 'organization'):
            obj.organization = self.instance.organization
        if commit:
            obj.save()
        return obj


class ObjectiveInline(admin.TabularInline):
    model = Objective
    formset = ObjectiveInlineFormSet
    extra = 1
    fields = ('title', 'description', 'order')
    ordering = ('order',)
    show_change_link = True


class RiskInlineFormSet(BaseInlineFormSet):
    def save_new(self, form, commit=True):
        obj = super().save_new(form, commit=False)
        if hasattr(self.instance, 'organization'):
            obj.organization = self.instance.organization
        if commit:
            obj.save()
        return obj


class RiskInline(admin.TabularInline):
    model = Risk
    formset = RiskInlineFormSet
    extra = 1
    fields = ('title', 'description', 'category', 'likelihood', 'impact')
    ordering = ('title',)
    show_change_link = True


class NoteInlineForm(forms.ModelForm):
    class Meta:
        model = Note
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        self.parent_instance = kwargs.pop('parent_instance', None)
        super().__init__(*args, **kwargs)

    def save(self, commit=True):
        obj = super().save(commit=False)
        if not obj.organization_id and self.parent_instance and hasattr(self.parent_instance, 'organization') and self.parent_instance.organization_id:
            obj.organization = self.parent_instance.organization
        if commit:
            obj.save()
        return obj


class FollowUpActionInlineFormSet(BaseInlineFormSet):
    def save_new(self, form, commit=True):
        obj = super().save_new(form, commit=False)
        if hasattr(self.instance, 'organization'):
            obj.organization = self.instance.organization
        if commit:
            obj.save()
        return obj


class IssueRetestInlineFormSet(BaseInlineFormSet):
    def save_new(self, form, commit=True):
        obj = super().save_new(form, commit=False)
        if hasattr(self.instance, 'organization'):
            obj.organization = self.instance.organization
        if commit:
            obj.save()
        return obj


class IssueInlineFormSet(BaseInlineFormSet):
    def save_new(self, form, commit=True):
        obj = super().save_new(form, commit=False)
        if hasattr(self.instance, 'organization'):
            obj.organization = self.instance.organization
        if commit:
            obj.save()
        return obj


class NoteInline(GenericTabularInline):
    model = Note
    form = NoteInlineForm
    ct_field = 'content_type'
    ct_fk_field = 'object_id'
    extra = 1
    fields = ('note_type', 'status', 'content', 'user', 'assigned_to', 'closed_by', 'cleared_at', 'closed_at', 'created_at')
    readonly_fields = ('created_at', 'cleared_at', 'closed_at')
    ordering = ('-created_at',)

    def get_formset(self, request, obj=None, **kwargs):
        formset = super().get_formset(request, obj, **kwargs)
        orig_get_form_kwargs = formset.get_form_kwargs
        def get_form_kwargs_with_parent(form, index):
            kwargs = orig_get_form_kwargs(form, index)
            kwargs['parent_instance'] = obj
            return kwargs
        formset.get_form_kwargs = get_form_kwargs_with_parent
        return formset


@admin.register(FollowUpAction)
class FollowUpActionAdmin(OrganizationScopedModelAdmin):
    list_display = ('issue', 'description', 'assigned_to', 'due_date', 'status', 'completed_at', 'created_by', 'created_at')
    list_filter = ('status', 'assigned_to', 'created_by', 'organization', 'issue')
    search_fields = ('description', 'notes')
    readonly_fields = ('created_at',)
    ordering = ('-created_at',)


@admin.register(IssueRetest)
class IssueRetestAdmin(OrganizationScopedModelAdmin):
    list_display = ('issue', 'retest_date', 'retested_by', 'result', 'created_at')
    list_filter = ('result', 'retested_by', 'organization', 'issue')
    search_fields = ('notes',)
    readonly_fields = ('created_at',)
    ordering = ('-retest_date',)


class FollowUpActionInline(admin.TabularInline):
    model = FollowUpAction
    formset = FollowUpActionInlineFormSet
    extra = 1
    fields = ('issue', 'description', 'assigned_to', 'due_date', 'status', 'completed_at', 'notes', 'created_by', 'created_at')
    readonly_fields = ('created_at',)
    ordering = ('-created_at',)


class IssueRetestInline(admin.TabularInline):
    model = IssueRetest
    formset = IssueRetestInlineFormSet
    extra = 1
    fields = ('issue', 'retest_date', 'retested_by', 'result', 'notes', 'created_at')
    readonly_fields = ('created_at',)
    ordering = ('-retest_date',)


class RecommendationInline(admin.TabularInline):
    model = Recommendation
    extra = 1
    fields = ('title', 'description', 'order')
    show_change_link = True


class NotificationInline(admin.TabularInline):
    model = Notification
    extra = 0
    fields = ('message', 'notification_type', 'is_read', 'created_at')
    readonly_fields = ('message', 'notification_type', 'created_at')
    can_delete = False
    ordering = ('-created_at',)


class IssueWorkingPaperInline(admin.TabularInline):
    model = IssueWorkingPaper
    extra = 1
    fields = ('file', 'description', 'uploaded_at', 'created_by', 'created_at')
    readonly_fields = ('uploaded_at', 'created_by', 'created_at')
    ordering = ('-uploaded_at',)


class IssueWorkingPaperAdmin(OrganizationScopedModelAdmin):
    list_display = ('issue', 'file', 'description', 'uploaded_at', 'created_by', 'organization')
    list_filter = ('organization', 'uploaded_at')
    search_fields = ('issue__issue_title', 'file', 'description')
    readonly_fields = ('uploaded_at', 'created_by', 'organization')
    ordering = ('-uploaded_at',)


@admin.register(AuditWorkplan)
class AuditWorkplanAdmin(OrganizationScopedVersionAdmin):
    list_display   = ("code", "name", "organization", "fiscal_year", "approval_status", "creation_date")
    list_filter    = ("organization", "fiscal_year", "approval_status")
    search_fields  = ("code", "name")
    inlines        = [ApprovalInline]
    date_hierarchy = "creation_date"
    
    # Make approval_status field read-only in the admin form
    readonly_fields = ("approval_status",)
    
    # Add state transition actions
    actions = ['submit_for_approval', 'approve', 'reject']
    
    def submit_for_approval(self, request, queryset):
        for workplan in queryset:
            if workplan.approval_status == 'draft':
                workplan.approval_status = 'submitted'
                workplan.save()
    submit_for_approval.short_description = "Submit selected workplans for approval"
    
    def approve(self, request, queryset):
        for workplan in queryset:
            if workplan.approval_status == 'submitted':
                workplan.approval_status = 'approved'
                workplan.save()
    approve.short_description = "Approve selected workplans"
    
    def reject(self, request, queryset):
        for workplan in queryset:
            if workplan.approval_status == 'submitted':
                workplan.approval_status = 'rejected'
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

    def save_formset(self, request, form, formset, change):
        instances = formset.save(commit=False)
        for obj in instances:
            if hasattr(obj, 'organization') and not obj.organization_id:
                obj.organization = form.instance.organization
            obj.save()
        formset.save_m2m()


@admin.register(Engagement)
class EngagementAdmin(OrganizationScopedVersionAdmin):
    list_display   = (
        "code", "title", "annual_workplan", "organization",
        "project_status", "assigned_to", "assigned_by",
        "project_start_date", "target_end_date", "approval_status",
    )
    list_filter    = ("organization", "project_status", "approval_status")
    search_fields  = ("code", "title", "annual_workplan__code")
    inlines        = [ObjectiveInline, NoteInline]
    date_hierarchy = "project_start_date"
    
    # Make approval_status field read-only in the admin form
    readonly_fields = ("approval_status",)
    
    # Add state transition actions
    actions = ['submit_for_approval', 'approve', 'reject']
    
    def submit_for_approval(self, request, queryset):
        for engagement in queryset:
            if engagement.approval_status == 'draft':
                engagement.approval_status = 'submitted'
                engagement.save()
    submit_for_approval.short_description = "Submit selected engagements for approval"
    
    def approve(self, request, queryset):
        for engagement in queryset:
            if engagement.approval_status == 'submitted':
                engagement.approval_status = 'approved'
                engagement.save()
    approve.short_description = "Approve selected engagements"
    
    def reject(self, request, queryset):
        for engagement in queryset:
            if engagement.approval_status == 'submitted':
                engagement.approval_status = 'rejected'
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

    def save_formset(self, request, form, formset, change):
        instances = formset.save(commit=False)
        for obj in instances:
            if hasattr(obj, 'organization') and not obj.organization_id:
                obj.organization = form.instance.organization
            obj.save()
        formset.save_m2m()


@admin.register(Issue)
class IssueAdmin(OrganizationScopedVersionAdmin):
    list_display   = (
        "code", "issue_title", "organization",
        "issue_status", "risk_level", "remediation_status", "date_identified",
    )
    list_filter    = ("organization", "issue_status", "risk_level", "remediation_status")
    search_fields  = ("code", "issue_title", "procedure_result__id")
    inlines        = [RecommendationInline, IssueWorkingPaperInline]
    date_hierarchy = "date_identified"
    readonly_fields = ("created_by", "created_at", "updated_by", "updated_at", "organization")

    def save_formset(self, request, form, formset, change):
        instances = formset.save(commit=False)
        for obj in instances:
            if not obj.organization_id:
                obj.organization = form.instance.organization
            if not obj.created_by_id:
                obj.created_by = request.user
            obj.save()
        formset.save_m2m()


@admin.register(Approval)
class ApprovalAdmin(OrganizationScopedModelAdmin):
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


@admin.register(Objective)
class ObjectiveAdmin(OrganizationScopedVersionAdmin):
    list_display = (
        "title", "engagement", "assigned_to", 
        "priority", "status", "estimated_hours",
        "created_at", "updated_at"
    )
    list_filter = ("engagement__organization", "status", "priority", "engagement")
    search_fields = ("title", "description", "criteria")
    inlines = [RiskInline]
    readonly_fields = ("created_at", "updated_at", "created_by", "updated_by")
    
    def save_model(self, request, obj, form, change):
        # Ensure organization is set from the engagement
        if obj.engagement and not obj.organization_id:
            obj.organization = obj.engagement.organization
        super().save_model(request, obj, form, change)


@admin.register(Procedure)
class ProcedureAdmin(OrganizationScopedVersionAdmin):
    list_display = (
        "title", "risk", "procedure_type", 
        "sample_size", "planned_date", "test_date"
    )
    list_filter = ("risk__organization", "procedure_type", "risk")
    search_fields = ("title", "description", "control_being_tested", "criteria")
    inlines = [ProcedureResultInline]
    readonly_fields = ("created_at", "updated_at", "created_by", "updated_by")
    
    def save_model(self, request, obj, form, change):
        # Ensure organization is set from the risk
        if obj.risk and not obj.organization_id:
            obj.organization = obj.risk.organization
        super().save_model(request, obj, form, change)


@admin.register(ProcedureResult)
class ProcedureResultAdmin(OrganizationScopedVersionAdmin):
    list_display = ('procedure', 'status', 'is_for_the_record', 'is_positive', 'order')
    list_filter = ('status', 'is_for_the_record', 'is_positive', 'procedure__risk__organization')
    search_fields = ('procedure__title', 'notes')
    readonly_fields = ("created_at", "updated_at", "created_by", "updated_by")
    
    def save_model(self, request, obj, form, change):
        # Ensure organization is set from the procedure
        if obj.procedure and not obj.organization_id:
            obj.organization = obj.procedure.organization
        super().save_model(request, obj, form, change)


@admin.register(Note)
class NoteAdmin(OrganizationScopedModelAdmin):
    list_display = ('note_type', 'status', 'user', 'assigned_to', 'closed_by', 'content_object', 'created_at', 'cleared_at', 'closed_at')
    list_filter = ('note_type', 'status', 'user', 'assigned_to', 'closed_by', 'organization')
    search_fields = ('content',)
    readonly_fields = ('created_at', 'cleared_at', 'closed_at')
    inlines = [NotificationInline]


# This class is now registered directly with @admin.register decorator above


@admin.register(Risk)
class RiskAdmin(OrganizationScopedVersionAdmin):
    list_display = (
        "title", "objective", "category", 
        "status", "inherent_risk_score", "residual_risk_score"
    )
    list_filter = ("objective__engagement__organization", "category", "status", "objective")
    search_fields = ("title", "description")
    inlines = [ProcedureInline]
    readonly_fields = ("created_at", "updated_at", "created_by", "updated_by")
    
    def save_model(self, request, obj, form, change):
        # Ensure organization is set from the objective
        if obj.objective and not obj.organization_id:
            obj.organization = obj.objective.organization
        super().save_model(request, obj, form, change)


@admin.register(Recommendation)
class RecommendationAdmin(OrganizationScopedModelAdmin):
    list_display = ('title', 'issue', 'order', 'organization', 'created_by', 'created_at')
    list_filter = ('issue', 'organization')
    search_fields = ('title', 'description')
    ordering = ('order',)
    readonly_fields = ("created_by", "created_at", "updated_by", "updated_at", "organization")

@admin.register(Notification)
class NotificationAdmin(OrganizationScopedModelAdmin):
    list_display = ('user', 'message', 'notification_type', 'is_read', 'created_at')
    list_filter = ('notification_type', 'is_read', 'user')
    search_fields = ('message',)
    readonly_fields = ('message', 'notification_type', 'created_at')
    ordering = ('-created_at',)

@admin.register(IssueWorkingPaper)
class IssueWorkingPaperAdmin(OrganizationScopedModelAdmin):
    list_display = ('issue', 'file', 'description', 'uploaded_at', 'created_by', 'organization')
    list_filter = ('organization', 'uploaded_at')
    search_fields = ('issue__issue_title', 'file', 'description')
    readonly_fields = ('uploaded_at', 'created_by', 'organization')
    ordering = ('-uploaded_at',)
