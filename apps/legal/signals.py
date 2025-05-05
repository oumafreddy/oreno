from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from .models import LegalCase, LegalDocument

# Example: Log when a legal case is created
@receiver(post_save, sender=LegalCase)
def legal_case_created(sender, instance, created, **kwargs):
    if created:
        # TODO: Add audit log or notification logic here
        pass

# Example: Log when a legal document is deleted
@receiver(post_delete, sender=LegalDocument)
def legal_document_deleted(sender, instance, **kwargs):
    # TODO: Add cleanup or audit logic here
    pass 