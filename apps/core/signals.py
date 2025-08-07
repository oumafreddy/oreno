from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver
from django.contrib.contenttypes.models import ContentType
from django.conf import settings
from .models import AuditLog
from django.db.utils import ProgrammingError, OperationalError, DatabaseError
from django.db import connection

def log_change(instance, action, changes=None, user=None):
    """Helper function to log model changes."""
    try:
        content_type = ContentType.objects.get_for_model(instance)
        # Truncate object_repr to fit within the 200 character limit
        object_repr = str(instance)
        if len(object_repr) > 200:
            object_repr = object_repr[:197] + "..."
        
        AuditLog.objects.create(
            content_type=content_type,
            object_id=instance.pk,
            action=action,
            changes=changes or {},
            object_repr=object_repr,
            user=user,
            model=f"{instance._meta.app_label}.{instance._meta.model_name}"
        )
    except (ProgrammingError, OperationalError, DatabaseError):
        # Silently fail if table doesn't exist
        pass
    except Exception as e:
        # Log any other errors but don't break the main operation
        import logging
        logger = logging.getLogger(__name__)
        logger.warning(f"Failed to log audit change for {instance}: {str(e)}")
        pass

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