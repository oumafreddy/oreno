# apps/audit/models/approval.py

import reversion
from django.db import models, transaction
from django.db.models import Q, Index
from django.contrib.postgres.indexes import GinIndex
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey
from django.core.exceptions import ValidationError

from common.constants import PENDING, APPROVED, REJECTED, STATUS_CHOICES

# Must match the migration’s list exactly
ALLOWED_CONTENT_MODELS = ['issue', 'auditworkplan', 'engagement']


class ApprovalQuerySet(models.QuerySet):
    def pending(self):
        return self.filter(status=PENDING)

    def approved(self):
        return self.filter(status=APPROVED)

    def rejected(self):
        return self.filter(status=REJECTED)

    def for_object(self, obj):
        return self.filter(
            content_type=ContentType.objects.get_for_model(obj),
            object_id=obj.pk
        )

    def for_approver(self, user):
        return self.filter(approver=user)


@reversion.register()
class Approval(models.Model):
    """
    Generic approval record. Links to any AuditWorkplan, Engagement or Issue.
    """
    content_type = models.ForeignKey(
        'contenttypes.contenttype',
        on_delete=models.CASCADE,
        limit_choices_to=Q(
            ('app_label', 'audit'),
            ('model__in', ALLOWED_CONTENT_MODELS)
        ),
    )
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey('content_type', 'object_id')

    organization = models.ForeignKey(
        'organizations.Organization',
        on_delete=models.CASCADE,
        related_name='approvals'
    )
    requester = models.ForeignKey(
        'users.CustomUser',
        related_name='requested_approvals',
        on_delete=models.CASCADE
    )
    approver = models.ForeignKey(
        'users.CustomUser',
        related_name='approvals_to_review',
        on_delete=models.CASCADE
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=PENDING,
        db_index=True,
        verbose_name="Approval State",
        help_text="Current approval state for this object.",
    )
    comments = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = ApprovalQuerySet.as_manager()

    class Meta:
        verbose_name = 'Approval'
        verbose_name_plural = 'Approvals'
        unique_together = (
            'content_type', 'object_id', 'approver', 'status'
        )
        ordering = ['-created_at']
        indexes = [
            Index(fields=['status'], name='pending_approvals_idx', condition=Q(status=PENDING)),
            Index(fields=['content_type', 'object_id']),
            Index(fields=['organization', 'status']),
        ]

    def __str__(self):
        return (
            f"{self.get_status_display()} for "
            f"{self.content_type.app_label}.{self.content_type.model}#{self.object_id} "
            f"→ {self.approver.get_full_name() or self.approver.email}"
        )

    def clean(self):
        # Prevent self-approval
        if self.requester_id == self.approver_id:
            raise ValidationError('Requester and approver cannot be the same user.')

        # Only one pending per object+approver
        qs = Approval.objects.filter(
            content_type=self.content_type,
            object_id=self.object_id,
            approver=self.approver,
            status=PENDING
        )
        if self.pk:
            qs = qs.exclude(pk=self.pk)
        if qs.exists():
            raise ValidationError('A pending approval already exists for this item and approver.')

        # Restrict to allowed content types
        if self.content_type.model not in ALLOWED_CONTENT_MODELS:
            raise ValidationError(f"Approval not allowed for {self.content_type.app_label}.{self.content_type.model}.")

    def save(self, *args, **kwargs):
        """
        Wrap in atomic + reversion revision.
        """
        try:
            with transaction.atomic(), reversion.create_revision():
                user = getattr(self, '_reversion_user', None)
                if user:
                    reversion.set_user(user)
                reversion.set_comment(f"Status changed to {self.status}")
                super().save(*args, **kwargs)
        except reversion.errors.RevisionManagementError:
            super().save(*args, **kwargs)

    def set_user_for_version(self, user):
        """
        Call before save() to record reversion user.
        """
        self._reversion_user = user
        return self
