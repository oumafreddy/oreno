from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from core.models.abstract_models import OrganizationOwnedModel, AuditableModel
from django_ckeditor_5.fields import CKEditor5Field
from organizations.models import Organization  # type: ignore[reportMissingImports]
import json

class ChatLog(models.Model):
    """Model to store chat conversation history"""
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='chat_logs',
        verbose_name=_('User')
    )
    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='chat_logs',
        verbose_name=_('Organization')
    )
    session_id = models.CharField(
        max_length=128,
        blank=True,
        null=True,
        db_index=True,
        verbose_name=_('Session ID'),
        help_text=_('Session identifier for grouping conversations')
    )
    query = models.TextField(
        verbose_name=_('Query'),
        help_text=_('User\'s query or question')
    )
    response = models.TextField(
        blank=True,
        null=True,
        verbose_name=_('Response'),
        help_text=_('AI assistant response')
    )
    metadata = models.JSONField(
        null=True,
        blank=True,
        verbose_name=_('Metadata'),
        help_text=_('Additional metadata (e.g., model, tokens, duration)')
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_('Created At')
    )

    class Meta:
        app_label = 'services_ai'  # Explicit app_label for Django
        db_table = 'services_ai_chatlog'  # Explicit table name
        verbose_name = _('Chat Log')
        verbose_name_plural = _('Chat Logs')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['organization', '-created_at']),
            models.Index(fields=['session_id', '-created_at']),
        ]

    def __str__(self):
        return f"{self.user} @ {self.created_at}: {self.query[:80]}"  # type: ignore[index]


class AIInteraction(AuditableModel):
    """
    Model to track lower-level LLM interactions and prompts for auditability
    Enhanced version with more detailed tracking
    """
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='ai_interactions',
        verbose_name=_('User')
    )
    organization = models.ForeignKey(
        Organization,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='ai_interactions',
        verbose_name=_('Organization')
    )
    prompt = models.TextField(
        verbose_name=_('Prompt'),
        help_text=_('The user prompt sent to LLM')
    )
    system_prompt = models.TextField(
        blank=True,
        null=True,
        verbose_name=_('System Prompt'),
        help_text=_('System prompt used for LLM')
    )
    response = models.TextField(
        blank=True,
        null=True,
        verbose_name=_('Response'),
        help_text=_('LLM response')
    )
    model = models.CharField(
        max_length=128,
        blank=True,
        null=True,
        verbose_name=_('Model'),
        help_text=_('LLM model used (e.g., gemma:2b, gpt-3.5-turbo)')
    )
    provider = models.CharField(
        max_length=64,
        default='deepseek',
        verbose_name=_('Provider'),
        help_text=_('LLM provider (deepseek, ollama, openai)')
    )
    tokens_used = models.IntegerField(
        null=True,
        blank=True,
        verbose_name=_('Tokens Used'),
        help_text=_('Number of tokens consumed')  # type: ignore[arg-type]
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_('Created At')
    )
    extra = models.JSONField(
        null=True,
        blank=True,
        verbose_name=_('Extra Data'),
        help_text=_('Additional metadata (e.g., job_id, raw_response)')
    )
    
    # Legacy fields for backward compatibility
    question = models.TextField(
        blank=True,
        null=True,
        verbose_name=_('Question'),
        help_text=_('Legacy: The user\'s question (use prompt instead)')
    )
    source = models.CharField(
        max_length=20,
        choices=[
            ('faq', 'FAQ'),
            ('deepseek', 'DeepSeek'),
            ('ollama', 'Ollama'),
            ('openai', 'OpenAI'),
        ],
        blank=True,
        null=True,
        verbose_name=_('Response Source'),
        help_text=_('Legacy: Which source provided the response')
    )
    processing_time = models.FloatField(
        null=True,
        blank=True,
        verbose_name=_('Processing Time (seconds)'),
        help_text=_('Time taken to generate response')  # type: ignore[arg-type]
    )
    success = models.BooleanField(
        default=True,  # type: ignore[arg-type]
        verbose_name=_('Success'),
        help_text=_('Whether the interaction was successful')  # type: ignore[arg-type]
    )
    error_message = models.TextField(
        blank=True,
        verbose_name=_('Error Message'),
        help_text=_('Error message if the interaction failed')
    )
    user_feedback = models.CharField(
        max_length=10,
        choices=[
            ('positive', 'Positive'),
            ('negative', 'Negative'),
            ('neutral', 'Neutral'),
        ],
        null=True,
        blank=True,
        verbose_name=_('User Feedback'),
        help_text=_('User feedback on the response quality')
    )
    metadata = models.JSONField(
        default=dict,
        blank=True,
        verbose_name=_('Metadata'),
        help_text=_('Additional metadata about the interaction')
    )
    
    class Meta:
        app_label = 'services_ai'  # Explicit app_label for Django
        db_table = 'services_ai_aiinteraction'  # Explicit table name
        verbose_name = _('AI Interaction')
        verbose_name_plural = _('AI Interactions')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['organization', '-created_at']),
            models.Index(fields=['provider', '-created_at']),
            models.Index(fields=['model', '-created_at']),
            models.Index(fields=['source', '-created_at']),
            models.Index(fields=['success', '-created_at']),
        ]
    
    def __str__(self):
        return f"AI Interaction by {self.user.username if self.user else 'Unknown'} on {self.created_at.strftime('%Y-%m-%d %H:%M')}"  # type: ignore[attr-defined]
    
    def save(self, *args, **kwargs):
        # Ensure metadata is a dict
        if not isinstance(self.metadata, dict):
            self.metadata = {}
        # Backward compatibility: set source from provider if not set
        if not self.source and self.provider:
            if self.provider == 'deepseek':
                self.source = 'deepseek'
            elif self.provider == 'ollama':
                self.source = 'ollama'
            elif self.provider == 'openai':
                self.source = 'openai'
        # Backward compatibility: set question from prompt if not set
        if not self.question and self.prompt:
            self.question = self.prompt
        super().save(*args, **kwargs)

class AIKnowledgeBase(AuditableModel):
    """
    Model to store and manage AI knowledge base entries
    """
    category = models.CharField(
        max_length=50,
        verbose_name=_('Category'),
        help_text=_('Category of the knowledge base entry')
    )
    
    question = models.TextField(
        verbose_name=_('Question'),
        help_text=_('The question or topic')
    )
    
    answer = models.TextField(
        verbose_name=_('Answer'),
        help_text=_('The answer or explanation')
    )
    
    keywords = models.JSONField(
        default=list,
        blank=True,
        verbose_name=_('Keywords'),
        help_text=_('Keywords for matching questions')
    )
    
    priority = models.IntegerField(
        default=1,  # type: ignore[arg-type]
        verbose_name=_('Priority'),
        help_text=_('Priority for matching (higher = more important)')  # type: ignore[arg-type]
    )
    
    is_active = models.BooleanField(
        default=True,  # type: ignore[arg-type]
        verbose_name=_('Active'),
        help_text=_('Whether this entry is active')  # type: ignore[arg-type]
    )
    
    usage_count = models.IntegerField(
        default=0,  # type: ignore[arg-type]
        verbose_name=_('Usage Count'),
        help_text=_('Number of times this entry has been used')  # type: ignore[arg-type]
    )
    
    class Meta:
        app_label = 'services_ai'  # Explicit app_label for Django
        db_table = 'services_ai_aiknowledgebase'  # Explicit table name
        verbose_name = _('AI Knowledge Base Entry')
        verbose_name_plural = _('AI Knowledge Base Entries')
        ordering = ['-priority', '-usage_count']
        indexes = [
            models.Index(fields=['category', 'is_active']),
            models.Index(fields=['is_active', '-priority']),
        ]
    
    def __str__(self):
        return f"{self.category}: {self.question[:50]}..."  # type: ignore[index]
    
    def save(self, *args, **kwargs):
        # Ensure keywords is a list
        if not isinstance(self.keywords, list):
            self.keywords = []
        super().save(*args, **kwargs)

class AIConfiguration(AuditableModel):
    """
    Model to store AI service configuration
    """
    key = models.CharField(
        max_length=100,
        unique=True,
        verbose_name=_('Configuration Key'),
        help_text=_('Configuration key')
    )
    
    value = models.JSONField(
        verbose_name=_('Configuration Value'),
        help_text=_('Configuration value (JSON)')
    )
    
    description = models.TextField(
        blank=True,
        verbose_name=_('Description'),
        help_text=_('Description of this configuration')
    )
    
    is_active = models.BooleanField(
        default=True,  # type: ignore[arg-type]
        verbose_name=_('Active'),
        help_text=_('Whether this configuration is active')  # type: ignore[arg-type]
    )
    
    class Meta:
        app_label = 'services_ai'  # Explicit app_label for Django
        db_table = 'services_ai_aiconfiguration'  # Explicit table name
        verbose_name = _('AI Configuration')
        verbose_name_plural = _('AI Configurations')
        ordering = ['key']
    
    def __str__(self):
        return f"{self.key}: {str(self.value)[:50]}..."


class PromptTemplate(AuditableModel):
    """Model to store reusable prompt templates"""
    key = models.CharField(
        max_length=100,
        unique=True,
        db_index=True,
        verbose_name=_('Key'),
        help_text=_('Unique identifier for the template')
    )
    title = models.CharField(
        max_length=200,
        verbose_name=_('Title'),
        help_text=_('Human-readable title')
    )
    description = models.TextField(
        blank=True,
        verbose_name=_('Description'),
        help_text=_('Description of what this template does')
    )
    template = models.TextField(
        verbose_name=_('Template'),
        help_text=_('Prompt template with placeholders like {{issue_description}}')
    )
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='prompt_templates',
        verbose_name=_('Owner'),
        help_text=_('User who created this template')
    )
    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='prompt_templates',
        verbose_name=_('Organization'),
        help_text=_('Organization this template belongs to (null for global)')
    )
    is_default = models.BooleanField(
        default=False,  # type: ignore[arg-type]
        verbose_name=_('Is Default'),
        help_text=_('Whether this is the default template for its key')  # type: ignore[arg-type]
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_('Created At')
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name=_('Updated At')
    )

    class Meta:
        app_label = 'services_ai'  # Explicit app_label for Django
        db_table = 'services_ai_prompttemplate'  # Explicit table name
        verbose_name = _('Prompt Template')
        verbose_name_plural = _('Prompt Templates')
        ordering = ['key']
        indexes = [
            models.Index(fields=['key', 'organization']),
            models.Index(fields=['is_default', 'organization']),
        ]

    def __str__(self):
        return f"{self.key} ({self.title})"
    
    def render(self, **kwargs):
        """Render the template with provided context"""
        result = self.template  # type: ignore[assignment]
        for key, value in kwargs.items():
            result = result.replace(f'{{{{{key}}}}}', str(value))  # type: ignore[attr-defined]
        return result
