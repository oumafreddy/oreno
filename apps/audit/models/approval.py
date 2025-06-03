# apps/audit/models/approval.py

import reversion
from django.db import models, transaction
from django.db.models import Q, Index
from django.contrib.postgres.indexes import GinIndex
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from simple_history.models import HistoricalRecords
from core.models.abstract_models import SoftDeletionModel, OrganizationOwnedModel

from common.constants import PENDING, APPROVED, REJECTED, STATUS_CHOICES

# Must match the migration's list exactly
# Updated for GIAS 2024 compliance with additional models
ALLOWED_CONTENT_MODELS = [
    'issue', 
    'annualworkplan',  # renamed from auditworkplan
    'engagement',
    'objective',
    'risk',
    'procedure',
    'recommendation',
    'issueretest',
    'followupaction'
]


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
class Approval(OrganizationOwnedModel, SoftDeletionModel):
    """
    Generic approval record for GIAS 2024 compliance.
    Links to any object that requires approval in the audit workflow.
    """
    content_type = models.ForeignKey(
        'contenttypes.contenttype',
        on_delete=models.CASCADE,
        limit_choices_to=Q(
            ('app_label', 'audit'),
            ('model__in', ALLOWED_CONTENT_MODELS)
        ),
        verbose_name=_('Content Type'),
        help_text=_('The type of object requiring approval')
    )
    object_id = models.PositiveIntegerField(
        verbose_name=_('Object ID'),
        help_text=_('The ID of the object requiring approval')
    )
    content_object = GenericForeignKey('content_type', 'object_id')
    requester = models.ForeignKey(
        'users.CustomUser',
        related_name='requested_approvals',
        on_delete=models.CASCADE,
        verbose_name=_('Requester'),
        help_text=_('User who requested the approval')
    )
    approver = models.ForeignKey(
        'users.CustomUser',
        related_name='approvals_to_review',
        on_delete=models.CASCADE,
        verbose_name=_('Approver'),
        help_text=_('User who needs to approve or reject')
    )
    
    APPROVAL_TYPE_CHOICES = [
        ('review', _('Review')),
        ('sign_off', _('Sign-off')),
        ('validation', _('Validation')),
        ('extension', _('Extension')),
        ('risk_acceptance', _('Risk Acceptance')),
        ('final_approval', _('Final Approval')),
    ]
    
    approval_type = models.CharField(
        max_length=20,
        choices=APPROVAL_TYPE_CHOICES,
        default='review',
        verbose_name=_('Approval Type'),
        help_text=_('Type of approval being requested')
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=PENDING,
        db_index=True,
        verbose_name=_('Approval State'),
        help_text=_('Current approval state for this object')
    )
    
    comments = models.TextField(
        blank=True,
        verbose_name=_('Comments'),
        help_text=_('Additional comments about the approval decision')
    )
    
    due_date = models.DateField(
        null=True,
        blank=True,
        verbose_name=_('Due Date'),
        help_text=_('Date by which approval should be completed')
    )
    
    reminder_sent = models.BooleanField(
        default=False,
        verbose_name=_('Reminder Sent'),
        help_text=_('Whether a reminder has been sent to the approver')
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    history = HistoricalRecords()

    objects = ApprovalQuerySet.as_manager()

    class Meta:
        verbose_name = _('Approval')
        verbose_name_plural = _('Approvals')
        unique_together = (
            'content_type', 'object_id', 'approver', 'approval_type'
        )
        ordering = ['-created_at']
        indexes = [
            Index(fields=['status'], name='pending_approvals_idx', condition=Q(status=PENDING)),
            Index(fields=['content_type', 'object_id']),
            Index(fields=['organization', 'status']),
            Index(fields=['approver', 'status']),
            Index(fields=['due_date']),
            Index(fields=['approval_type']),
        ]
        constraints = [
            models.CheckConstraint(
                check=models.Q(organization__isnull=False),
                name='organization_required_approval'
            )
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
            raise ValidationError(_('Requester and approver cannot be the same user.'))

        # Only one pending per object+approver+approval_type
        qs = Approval.objects.filter(
            content_type=self.content_type,
            object_id=self.object_id,
            approver=self.approver,
            approval_type=self.approval_type,
            status=PENDING
        )
        if self.pk:
            qs = qs.exclude(pk=self.pk)
        if qs.exists():
            raise ValidationError(_('A pending approval already exists for this item and approver with the same approval type.'))

        # Restrict to allowed content types
        if self.content_type.model not in ALLOWED_CONTENT_MODELS:
            raise ValidationError(_(f"Approval not allowed for {self.content_type.app_label}.{self.content_type.model}."))

    def save(self, *args, **kwargs):
        """
        Wrap in atomic + reversion revision.
        Add additional GIAS 2024 validation.
        """
        try:
            with transaction.atomic(), reversion.create_revision():
                user = getattr(self, '_reversion_user', None)
                if user:
                    reversion.set_user(user)
                    
                # Add comment based on status change
                if self.status == APPROVED:
                    comment = f"Approved by {user.get_full_name() or user.email}"
                elif self.status == REJECTED:
                    comment = f"Rejected by {user.get_full_name() or user.email}"
                else:
                    comment = f"Status changed to {self.get_status_display()}"
                    
                reversion.set_comment(comment)
                super().save(*args, **kwargs)
        except reversion.errors.RevisionManagementError:
            super().save(*args, **kwargs)

    def set_user_for_version(self, user):
        """
        Call before save() to record reversion user.
        """
        self._reversion_user = user
        return self
