from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from apps.core.models.abstract_models import OrganizationOwnedModel, AuditableModel
from django_ckeditor_5.fields import CKEditor5Field
import json

class AIInteraction(AuditableModel):
    """
    Model to track AI interactions for audit and improvement purposes
    """
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='ai_interactions',
        verbose_name=_('User')
    )
    
    question = models.TextField(
        verbose_name=_('Question'),
        help_text=_('The user\'s question')
    )
    
    response = models.TextField(
        verbose_name=_('AI Response'),
        help_text=_('The AI\'s response')
    )
    
    source = models.CharField(
        max_length=20,
        choices=[
            ('faq', 'FAQ'),
            ('ollama', 'Ollama'),
            ('openai', 'OpenAI'),
        ],
        verbose_name=_('Response Source'),
        help_text=_('Which source provided the response')
    )
    
    processing_time = models.FloatField(
        null=True,
        blank=True,
        verbose_name=_('Processing Time (seconds)'),
        help_text=_('Time taken to generate response')
    )
    
    success = models.BooleanField(
        default=True,
        verbose_name=_('Success'),
        help_text=_('Whether the interaction was successful')
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
        verbose_name = _('AI Interaction')
        verbose_name_plural = _('AI Interactions')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['source', '-created_at']),
            models.Index(fields=['success', '-created_at']),
        ]
    
    def __str__(self):
        return f"AI Interaction by {self.user.username} on {self.created_at.strftime('%Y-%m-%d %H:%M')}"
    
    def save(self, *args, **kwargs):
        # Ensure metadata is a dict
        if not isinstance(self.metadata, dict):
            self.metadata = {}
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
        default=1,
        verbose_name=_('Priority'),
        help_text=_('Priority for matching (higher = more important)')
    )
    
    is_active = models.BooleanField(
        default=True,
        verbose_name=_('Active'),
        help_text=_('Whether this entry is active')
    )
    
    usage_count = models.IntegerField(
        default=0,
        verbose_name=_('Usage Count'),
        help_text=_('Number of times this entry has been used')
    )
    
    class Meta:
        verbose_name = _('AI Knowledge Base Entry')
        verbose_name_plural = _('AI Knowledge Base Entries')
        ordering = ['-priority', '-usage_count']
        indexes = [
            models.Index(fields=['category', 'is_active']),
            models.Index(fields=['is_active', '-priority']),
        ]
    
    def __str__(self):
        return f"{self.category}: {self.question[:50]}..."
    
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
        default=True,
        verbose_name=_('Active'),
        help_text=_('Whether this configuration is active')
    )
    
    class Meta:
        verbose_name = _('AI Configuration')
        verbose_name_plural = _('AI Configurations')
        ordering = ['key']
    
    def __str__(self):
        return f"{self.key}: {str(self.value)[:50]}..."
