from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from .models import AIInteraction, AIKnowledgeBase, AIConfiguration

@admin.register(AIInteraction)
class AIInteractionAdmin(admin.ModelAdmin):
    list_display = [
        'user', 'question_preview', 'source', 'success', 
        'processing_time', 'created_at', 'user_feedback'
    ]
    list_filter = [
        'source', 'success', 'user_feedback', 'created_at',
        ('user', admin.RelatedOnlyFieldListFilter)
    ]
    search_fields = ['question', 'response', 'user__username', 'user__email']
    readonly_fields = ['created_at', 'updated_at', 'created_by', 'updated_by']
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('user', 'question', 'response', 'source')
        }),
        ('Performance', {
            'fields': ('processing_time', 'success', 'error_message')
        }),
        ('Feedback', {
            'fields': ('user_feedback', 'metadata')
        }),
        ('Audit Information', {
            'fields': ('created_at', 'updated_at', 'created_by', 'updated_by'),
            'classes': ('collapse',)
        }),
    )
    
    def question_preview(self, obj):
        """Show a preview of the question"""
        return obj.question[:50] + "..." if len(obj.question) > 50 else obj.question
    question_preview.short_description = 'Question'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user')

@admin.register(AIKnowledgeBase)
class AIKnowledgeBaseAdmin(admin.ModelAdmin):
    list_display = [
        'category', 'question_preview', 'priority', 'is_active', 
        'usage_count', 'created_at'
    ]
    list_filter = ['category', 'is_active', 'priority', 'created_at']
    search_fields = ['question', 'answer', 'category']
    readonly_fields = ['usage_count', 'created_at', 'updated_at', 'created_by', 'updated_by']
    list_editable = ['priority', 'is_active']
    
    fieldsets = (
        ('Content', {
            'fields': ('category', 'question', 'answer', 'keywords')
        }),
        ('Settings', {
            'fields': ('priority', 'is_active', 'usage_count')
        }),
        ('Audit Information', {
            'fields': ('created_at', 'updated_at', 'created_by', 'updated_by'),
            'classes': ('collapse',)
        }),
    )
    
    def question_preview(self, obj):
        """Show a preview of the question"""
        return obj.question[:50] + "..." if len(obj.question) > 50 else obj.question
    question_preview.short_description = 'Question'
    
    actions = ['activate_entries', 'deactivate_entries']
    
    def activate_entries(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(request, f'{updated} knowledge base entries activated.')
    activate_entries.short_description = "Activate selected entries"
    
    def deactivate_entries(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(request, f'{updated} knowledge base entries deactivated.')
    deactivate_entries.short_description = "Deactivate selected entries"

@admin.register(AIConfiguration)
class AIConfigurationAdmin(admin.ModelAdmin):
    list_display = ['key', 'value_preview', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['key', 'description']
    readonly_fields = ['created_at', 'updated_at', 'created_by', 'updated_by']
    list_editable = ['is_active']
    
    fieldsets = (
        ('Configuration', {
            'fields': ('key', 'value', 'description', 'is_active')
        }),
        ('Audit Information', {
            'fields': ('created_at', 'updated_at', 'created_by', 'updated_by'),
            'classes': ('collapse',)
        }),
    )
    
    def value_preview(self, obj):
        """Show a preview of the configuration value"""
        value_str = str(obj.value)
        return value_str[:50] + "..." if len(value_str) > 50 else value_str
    value_preview.short_description = 'Value'

# Custom admin site configuration
admin.site.site_header = "Oreno GRC AI Administration"
admin.site.site_title = "Oreno GRC AI Admin"
admin.site.index_title = "AI Service Management"
