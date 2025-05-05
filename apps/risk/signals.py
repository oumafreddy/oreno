from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from .models import Risk, Control

@receiver(post_save, sender=Risk)
def risk_post_save(sender, instance, created, **kwargs):
    # TODO: Implement audit logging or notifications
    if created:
        pass  # e.g., log creation
    else:
        pass  # e.g., log update

@receiver(post_delete, sender=Risk)
def risk_post_delete(sender, instance, **kwargs):
    # TODO: Implement audit logging or notifications
    pass

@receiver(post_save, sender=Control)
def control_post_save(sender, instance, created, **kwargs):
    # TODO: Implement audit logging or notifications
    pass

@receiver(post_delete, sender=Control)
def control_post_delete(sender, instance, **kwargs):
    # TODO: Implement audit logging or notifications
    pass 