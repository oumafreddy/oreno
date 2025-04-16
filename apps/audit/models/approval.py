# audits/models/approval.py

from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
import reversion  # Ensure django-reversion is installed
from django.db import models, transaction
from django.db.models import Q, Index
from django.contrib.postgres.indexes import GinIndex

class Approval(models.Model):
    PENDING = 'pending'
    APPROVED = 'approved'
    REJECTED = 'rejected'
    STATUS_CHOICES = (
        (PENDING, 'Pending Approval'),
        (APPROVED, 'Approved'),
        (REJECTED, 'Rejected'),
    )

    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey('content_type', 'object_id')

    organization = models.ForeignKey('organizations.Organization', on_delete=models.CASCADE)
    requester = models.ForeignKey('users.CustomUser', related_name='requested_approvals', on_delete=models.CASCADE)
    approver = models.ForeignKey('users.CustomUser', related_name='approvals_to_review', on_delete=models.CASCADE)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=PENDING)
    comments = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save_version(self, *args, **kwargs):
        """
        Save the approval with versioning support.
        Wrap the save in an atomic transaction and create a revision using django-reversion.
        """
        with transaction.atomic(), reversion.create_revision():
            reversion.set_user(self.requester)
            reversion.set_comment(f"Approval state changed to {self.status}")
            super().save(*args, **kwargs)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            # If you eventually add a 'search_vector' field, you can include a GinIndex:
            # GinIndex(fields=['search_vector']),
            # Partial index on status pending:
            Index(fields=['status'], name='pending_approvals_idx', condition=Q(status='pending')),
            Index(fields=['content_type', 'object_id']),
            Index(fields=['organization', 'status']),
        ]
