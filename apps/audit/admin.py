# apps/audit/admin.py

from django.contrib import admin
from django.contrib.contenttypes.admin import GenericTabularInline
from django.utils.translation import gettext_lazy as _
import reversion.admin
from django.forms.models import BaseInlineFormSet
from django import forms

from .models.workplan import AuditWorkplan
from .models.engagement import Engagement
from .models.issue import Issue
from .models.approval import Approval
from .models import (
    Objective, Procedure, ProcedureResult, Note
)
from .models.followupaction import FollowUpAction
from .models.issueretest import IssueRetest
from .models.recommendation import Recommendation
from .models.note import Notification
from .models.issue_working_paper import IssueWorkingPaper


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
    fields = ('title', 'description', 'related_risks', 'order')
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
class FollowUpActionAdmin(admin.ModelAdmin):
    list_display = ('issue', 'description', 'assigned_to', 'due_date', 'status', 'completed_at', 'created_by', 'created_at')
    list_filter = ('status', 'assigned_to', 'created_by', 'organization', 'issue')
    search_fields = ('description', 'notes')
    readonly_fields = ('created_at',)
    ordering = ('-created_at',)


@admin.register(IssueRetest)
class IssueRetestAdmin(admin.ModelAdmin):
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


class IssueWorkingPaperAdmin(admin.ModelAdmin):
    list_display = ('issue', 'file', 'description', 'uploaded_at', 'created_by', 'organization')
    list_filter = ('organization', 'uploaded_at')
    search_fields = ('issue__issue_title', 'file', 'description')
    readonly_fields = ('uploaded_at', 'created_by', 'organization')
    ordering = ('-uploaded_at',)


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

    def save_formset(self, request, form, formset, change):
        instances = formset.save(commit=False)
        for obj in instances:
            if hasattr(obj, 'organization') and not obj.organization_id:
                obj.organization = form.instance.organization
            obj.save()
        formset.save_m2m()


@admin.register(Engagement)
class EngagementAdmin(reversion.admin.VersionAdmin):
    list_display   = (
        "code", "title", "audit_workplan", "organization",
        "project_status", "assigned_to", "assigned_by",
        "project_start_date", "target_end_date", "state",
    )
    list_filter    = ("organization", "project_status", "state")
    search_fields  = ("code", "title", "audit_workplan__code")
    inlines        = [ObjectiveInline, NoteInline]
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

    def save_formset(self, request, form, formset, change):
        instances = formset.save(commit=False)
        for obj in instances:
            if hasattr(obj, 'organization') and not obj.organization_id:
                obj.organization = form.instance.organization
            obj.save()
        formset.save_m2m()


@admin.register(Issue)
class IssueAdmin(reversion.admin.VersionAdmin):
    list_display   = (
        "code", "issue_title", "organization", "procedure_result",
        "issue_status", "severity_status", "remediation_status", "date_identified",
    )
    list_filter    = ("organization", "issue_status", "severity_status", "remediation_status")
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


@admin.register(Objective)
class ObjectiveAdmin(admin.ModelAdmin):
    list_display = ('title', 'engagement', 'order')
    list_filter = ('engagement', 'organization')
    search_fields = ('title',)
    inlines = [ProcedureInline]
    readonly_fields = ("created_by", "created_at", "updated_by", "updated_at", "organization")


@admin.register(Procedure)
class ProcedureAdmin(admin.ModelAdmin):
    list_display = ('title', 'objective', 'order')
    list_filter = ('objective', 'organization')
    search_fields = ('title',)
    inlines = [ProcedureResultInline]
    readonly_fields = ("created_by", "created_at", "updated_by", "updated_at", "organization")


@admin.register(ProcedureResult)
class ProcedureResultAdmin(admin.ModelAdmin):
    list_display = ('procedure', 'status', 'is_for_the_record', 'order')
    list_filter = ('status', 'is_for_the_record', 'procedure__objective__engagement__organization')
    search_fields = ('procedure__title', 'notes')


@admin.register(Note)
class NoteAdmin(admin.ModelAdmin):
    list_display = ('note_type', 'status', 'user', 'assigned_to', 'closed_by', 'content_object', 'created_at', 'cleared_at', 'closed_at')
    list_filter = ('note_type', 'status', 'user', 'assigned_to', 'closed_by', 'organization')
    search_fields = ('content',)
    readonly_fields = ('created_at', 'cleared_at', 'closed_at')
    inlines = [NotificationInline]


class RecommendationAdmin(admin.ModelAdmin):
    list_display = ('title', 'issue', 'order', 'organization', 'created_by', 'created_at')
    list_filter = ('issue', 'organization')
    search_fields = ('title', 'description')
    ordering = ('order',)
    readonly_fields = ("created_by", "created_at", "updated_by", "updated_at", "organization")


admin.site.register(Recommendation, RecommendationAdmin)

@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('user', 'message', 'notification_type', 'is_read', 'created_at')
    list_filter = ('notification_type', 'is_read', 'user')
    search_fields = ('message',)
    readonly_fields = ('message', 'notification_type', 'created_at')
    ordering = ('-created_at',)

admin.site.register(IssueWorkingPaper, IssueWorkingPaperAdmin)
