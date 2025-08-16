from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from core.models.abstract_models import OrganizationOwnedModel, AuditableModel
from django_ckeditor_5.fields import CKEditor5Field
import json

class AIConversation(OrganizationOwnedModel, AuditableModel):
    """
    Tracks AI conversation sessions for context and history.
    """
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='ai_conversations',
        verbose_name=_('User')
    )
    session_id = models.CharField(
        max_length=64,
        db_index=True,
        verbose_name=_('Session ID'),
        help_text=_('Unique session identifier')
    )
    title = models.CharField(
        max_length=255,
        blank=True,
        verbose_name=_('Conversation Title'),
        help_text=_('Auto-generated title based on first question')
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name=_('Active'),
        help_text=_('Whether this conversation is still active')
    )
    total_tokens = models.PositiveIntegerField(
        default=0,
        verbose_name=_('Total Tokens'),
        help_text=_('Total tokens used in this conversation')
    )
    model_used = models.CharField(
        max_length=50,
        verbose_name=_('Model Used'),
        help_text=_('AI model used for responses')
    )
    
    class Meta:
        app_label = 'ai'
        verbose_name = _('AI Conversation')
        verbose_name_plural = _('AI Conversations')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'organization']),
            models.Index(fields=['session_id']),
            models.Index(fields=['is_active']),
        ]

    def __str__(self):
        return f"AI Conversation - {self.user.email} - {self.title}"

class AIMessage(OrganizationOwnedModel, AuditableModel):
    """
    Individual messages within AI conversations.
    """
    conversation = models.ForeignKey(
        AIConversation,
        on_delete=models.CASCADE,
        related_name='messages',
        verbose_name=_('Conversation')
    )
    role = models.CharField(
        max_length=20,
        choices=[
            ('user', _('User')),
            ('assistant', _('Assistant')),
            ('system', _('System')),
        ],
        verbose_name=_('Role')
    )
    content = models.TextField(
        verbose_name=_('Content'),
        help_text=_('Message content')
    )
    tokens_used = models.PositiveIntegerField(
        default=0,
        verbose_name=_('Tokens Used'),
        help_text=_('Number of tokens used for this message')
    )
    model_used = models.CharField(
        max_length=50,
        verbose_name=_('Model Used'),
        help_text=_('AI model used for this message')
    )
    response_time = models.FloatField(
        null=True,
        blank=True,
        verbose_name=_('Response Time'),
        help_text=_('Response time in seconds')
    )
    metadata = models.JSONField(
        default=dict,
        blank=True,
        verbose_name=_('Metadata'),
        help_text=_('Additional metadata about the message')
    )
    
    class Meta:
        app_label = 'ai'
        verbose_name = _('AI Message')
        verbose_name_plural = _('AI Messages')
        ordering = ['created_at']
        indexes = [
            models.Index(fields=['conversation', 'role']),
            models.Index(fields=['created_at']),
        ]

    def __str__(self):
        return f"{self.role} message in {self.conversation}"

class AIUserPreference(OrganizationOwnedModel, AuditableModel):
    """
    User preferences for AI interactions.
    """
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='ai_preferences',
        verbose_name=_('User')
    )
    preferred_model = models.CharField(
        max_length=50,
        default='llama3:8b',
        verbose_name=_('Preferred Model'),
        help_text=_('User\'s preferred AI model')
    )
    max_tokens = models.PositiveIntegerField(
        default=2048,
        verbose_name=_('Max Tokens'),
        help_text=_('Maximum tokens per response')
    )
    temperature = models.FloatField(
        default=0.7,
        verbose_name=_('Temperature'),
        help_text=_('AI response creativity (0.0-1.0)')
    )
    context_window = models.PositiveIntegerField(
        default=10,
        verbose_name=_('Context Window'),
        help_text=_('Number of previous messages to include in context')
    )
    auto_save_conversations = models.BooleanField(
        default=True,
        verbose_name=_('Auto Save Conversations'),
        help_text=_('Automatically save conversation history')
    )
    notifications_enabled = models.BooleanField(
        default=True,
        verbose_name=_('Notifications Enabled'),
        help_text=_('Enable AI-related notifications')
    )
    
    class Meta:
        app_label = 'ai'
        verbose_name = _('AI User Preference')
        verbose_name_plural = _('AI User Preferences')

    def __str__(self):
        return f"AI Preferences for {self.user.email}"

class AIKnowledgeBase(OrganizationOwnedModel, AuditableModel):
    """
    Extensible knowledge base for AI responses.
    """
    title = models.CharField(
        max_length=255,
        verbose_name=_('Title'),
        help_text=_('Knowledge base entry title')
    )
    category = models.CharField(
        max_length=100,
        choices=[
            ('grc_general', _('GRC General')),
            ('audit', _('Audit')),
            ('risk', _('Risk')),
            ('compliance', _('Compliance')),
            ('legal', _('Legal')),
            ('platform', _('Platform')),
            ('best_practices', _('Best Practices')),
        ],
        verbose_name=_('Category')
    )
    keywords = models.JSONField(
        default=list,
        blank=True,
        verbose_name=_('Keywords'),
        help_text=_('Keywords for matching questions')
    )
    question_patterns = models.JSONField(
        default=list,
        blank=True,
        verbose_name=_('Question Patterns'),
        help_text=_('Common question patterns')
    )
    content = CKEditor5Field(
        config_name='extends',
        verbose_name=_('Content'),
        help_text=_('Knowledge base content')
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name=_('Active'),
        help_text=_('Whether this knowledge base entry is active')
    )
    priority = models.PositiveIntegerField(
        default=1,
        verbose_name=_('Priority'),
        help_text=_('Priority for matching (higher = more important)')
    )
    usage_count = models.PositiveIntegerField(
        default=0,
        verbose_name=_('Usage Count'),
        help_text=_('Number of times this entry has been used')
    )
    
    class Meta:
        app_label = 'ai'
        verbose_name = _('AI Knowledge Base')
        verbose_name_plural = _('AI Knowledge Base')
        ordering = ['-priority', '-usage_count']
        indexes = [
            models.Index(fields=['category', 'is_active']),
            models.Index(fields=['keywords']),
        ]

    def __str__(self):
        return f"{self.title} ({self.get_category_display()})"

class AIAnalytics(OrganizationOwnedModel, AuditableModel):
    """
    Analytics and usage tracking for AI service.
    """
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='ai_analytics',
        verbose_name=_('User')
    )
    event_type = models.CharField(
        max_length=50,
        choices=[
            ('conversation_started', _('Conversation Started')),
            ('message_sent', _('Message Sent')),
            ('response_received', _('Response Received')),
            ('conversation_ended', _('Conversation Ended')),
            ('model_switched', _('Model Switched')),
            ('error_occurred', _('Error Occurred')),
        ],
        verbose_name=_('Event Type')
    )
    model_used = models.CharField(
        max_length=50,
        verbose_name=_('Model Used')
    )
    tokens_used = models.PositiveIntegerField(
        default=0,
        verbose_name=_('Tokens Used')
    )
    response_time = models.FloatField(
        null=True,
        blank=True,
        verbose_name=_('Response Time')
    )
    metadata = models.JSONField(
        default=dict,
        blank=True,
        verbose_name=_('Metadata')
    )
    
    class Meta:
        app_label = 'ai'
        verbose_name = _('AI Analytics')
        verbose_name_plural = _('AI Analytics')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'event_type']),
            models.Index(fields=['created_at']),
            models.Index(fields=['model_used']),
        ]

    def __str__(self):
        return f"{self.event_type} - {self.user.email} - {self.created_at}"
