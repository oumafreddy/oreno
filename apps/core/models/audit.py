from django.db import models
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _
from django.apps import apps

class AuditLog(models.Model):
    """
    Model for tracking changes to model instances
    """
    ACTION_CHOICES = (
        ('create', _('Created')),
        ('update', _('Updated')),
        ('delete', _('Deleted')),
    )

    content_type = models.ForeignKey(
        ContentType,
        on_delete=models.CASCADE,
        verbose_name=_('content type'),
        help_text=_('The type of object that was changed')
    )
    object_id = models.PositiveIntegerField(
        verbose_name=_('object id'),
        help_text=_('The ID of the object that was changed')
    )
    content_object = GenericForeignKey('content_type', 'object_id')
    
    user = models.ForeignKey(
        get_user_model(),
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        verbose_name=_('user'),
        help_text=_('The user who made the change')
    )
    
    action = models.CharField(
        max_length=50,
        choices=ACTION_CHOICES,
        verbose_name=_('action'),
        help_text=_('The type of change that was made')
    )
    
    changes = models.JSONField(
        default=dict,
        blank=True,
        verbose_name=_('changes'),
        help_text=_('The changes that were made to the object')
    )
    
    object_repr = models.CharField(
        max_length=200,
        verbose_name=_('object representation'),
        help_text=_('String representation of the object')
    )
    
    timestamp = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_('timestamp'),
        help_text=_('When this change was made')
    )

    model = models.CharField(max_length=100)
    details = models.JSONField(default=dict)
    ip_address = models.GenericIPAddressField(null=True)
    user_agent = models.TextField(null=True)
    created_by = models.ForeignKey(
        get_user_model(),
        on_delete=models.SET_NULL,
        null=True,
        related_name='audit_logs_created'
    )

    class Meta:
        app_label = 'core'
        verbose_name = _('audit log')
        verbose_name_plural = _('audit logs')
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['content_type', 'object_id']),
            models.Index(fields=['timestamp']),
            models.Index(fields=['action']),
        ]

    def __str__(self):
        return f"{self.get_action_display()} - {self.content_type} - {self.object_repr}"

    @property
    def changed_fields(self):
        return list(self.changes.keys()) if self.changes else []

    def get_change(self, field_name):
        return self.changes.get(field_name, {})

    def get_object(self):
        return self.content_object

    def get_action_display(self):
        return dict(self.ACTION_CHOICES)[self.action] 