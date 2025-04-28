from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver
from django.contrib.contenttypes.models import ContentType
from django.conf import settings
from .models import AuditLog

def log_change(instance, action, changes=None, user=None):
    """Helper function to log model changes."""
    content_type = ContentType.objects.get_for_model(instance)
    AuditLog.objects.create(
        content_type=content_type,
        object_id=instance.pk,
        action=action,
        changes=changes or {},
        object_repr=str(instance),
        user=user,
        model=f"{instance._meta.app_label}.{instance._meta.model_name}"
    )

@receiver(post_save)
def log_save(sender, instance, created, **kwargs):
    """Log model creation and updates."""
    if sender._meta.app_label in settings.AUDIT_ENABLED_APPS:
        action = 'create' if created else 'update'
        log_change(instance, action)

@receiver(pre_delete)
def log_delete(sender, instance, **kwargs):
    """Log model deletion."""
    if sender._meta.app_label in settings.AUDIT_ENABLED_APPS:
        log_change(instance, 'delete') 