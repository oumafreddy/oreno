from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from .models import DocumentRequest, Document

@receiver(post_save, sender=DocumentRequest)
def log_documentrequest_save(sender, instance, created, **kwargs):
    if created:
        print(f"[Audit] DocumentRequest created: {instance}")
    else:
        print(f"[Audit] DocumentRequest updated: {instance}")

@receiver(post_delete, sender=DocumentRequest)
def log_documentrequest_delete(sender, instance, **kwargs):
    print(f"[Audit] DocumentRequest deleted: {instance}")

@receiver(post_save, sender=Document)
def log_document_save(sender, instance, created, **kwargs):
    if created:
        print(f"[Audit] Document created: {instance}")
    else:
        print(f"[Audit] Document updated: {instance}")

@receiver(post_delete, sender=Document)
def log_document_delete(sender, instance, **kwargs):
    print(f"[Audit] Document deleted: {instance}") 