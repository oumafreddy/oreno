from django.db import models
from django.utils.translation import gettext_lazy as _
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.conf import settings
from core.models.abstract_models import OrganizationOwnedModel, AuditableModel, SoftDeletionModel
from django_ckeditor_5.fields import CKEditor5Field
from django.utils import timezone
from simple_history.models import HistoricalRecords

class Note(OrganizationOwnedModel, AuditableModel, SoftDeletionModel):
    NOTE_TYPE_CHOICES = [
        ('todo', _('To-Do')),
        ('review', _('Review')),
        ('review_request', _('Review Request')),
        ('general', _('General')),
    ]
    STATUS_CHOICES = [
        ('open', _('Open')),
        ('cleared', _('Cleared by Owner')),
        ('closed', _('Closed by Supervisor')),
    ]
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey('content_type', 'object_id')
    note_type = models.CharField(max_length=16, choices=NOTE_TYPE_CHOICES, default='general', verbose_name=_('Note Type'))
    content = CKEditor5Field(_('Note Content'), config_name='extends', blank=True, null=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, verbose_name=_('User'))
    created_at = models.DateTimeField(auto_now_add=True)
    organization = models.ForeignKey(
        'organizations.Organization',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='notes',
        verbose_name=_('Organization')
    )
    status = models.CharField(
        max_length=16,
        choices=STATUS_CHOICES,
        default='open',
        verbose_name=_('Status')
    )
    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='notes_assigned',
        verbose_name=_('Assigned To')
    )
    closed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='notes_closed',
        verbose_name=_('Closed By')
    )
    cleared_at = models.DateTimeField(null=True, blank=True, verbose_name=_('Cleared At'))
    closed_at = models.DateTimeField(null=True, blank=True, verbose_name=_('Closed At'))
    history = HistoricalRecords()

    class Meta:
        app_label = 'audit'
        verbose_name = _('Note')
        verbose_name_plural = _('Notes')
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.get_note_type_display()} Note by {self.user} on {self.content_object}"

    def mark_cleared(self, user):
        self.status = 'cleared'
        self.cleared_at = timezone.now()
        self.save(update_fields=['status', 'cleared_at'])

    def mark_closed(self, user):
        self.status = 'closed'
        self.closed_by = user
        self.closed_at = timezone.now()
        self.save(update_fields=['status', 'closed_by', 'closed_at'])

class Notification(models.Model):
    # Organization field for multi-tenancy compliance (explicitly defined)
    organization = models.ForeignKey(
        'organizations.Organization',
        on_delete=models.CASCADE,
        verbose_name=_('organization'),
        related_name="notification_items",
        null=False  # Required for organization-level filtering
    )
    
    # Audit trail fields (explicitly defined instead of inherited)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='notification_created',
        verbose_name=_('created by')
    )
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='notification_updated',
        verbose_name=_('updated by')
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_('updated at'))
    
    # Core notification fields
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='notifications')
    note = models.ForeignKey('Note', on_delete=models.CASCADE, related_name='notifications', null=True, blank=True)
    message = models.TextField()
    notification_type = models.CharField(max_length=32, default='note')
    is_read = models.BooleanField(default=False)
    
    class Meta:
        app_label = 'audit'
        verbose_name = _('Notification')
        verbose_name_plural = _('Notifications')
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Notification for {self.user} - {self.message[:40]}..."
        
    @classmethod
    def create_for_user(cls, user, message, notification_type='note', note=None):
        """Factory method to create a notification with proper organization assignment"""
        notification = cls(
            user=user,
            message=message,
            notification_type=notification_type,
            note=note,
            organization=user.organization,
            created_by=user,
            updated_by=user
        )
        notification.save()
        return notification
        
    def save(self, *args, **kwargs):
        # Ensure organization is set from user if not already provided
        if not self.organization and self.user and hasattr(self.user, 'organization'):
            self.organization = self.user.organization
            
        if not self.organization:
            raise ValueError("Notification must have an organization assigned.")
        
        # Handle audit trail fields
        if not self.pk and not self.created_by and self.user:
            self.created_by = self.user
        
        if self.user:
            self.updated_by = self.user
            
        super().save(*args, **kwargs) 