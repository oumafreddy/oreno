from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from django_ckeditor_5.fields import CKEditor5Field

class TimeStampedModel(models.Model):
    """
    Base abstract model providing self-updating timestamps with database indexing.
    Ensures all child models have creation/update tracking optimized for queries.
    """
    created_at = models.DateTimeField(
        _('created at'),
        auto_now_add=True,
        db_index=True,
        help_text=_("Timestamp when the record was first created")
    )
    updated_at = models.DateTimeField(
        _('updated at'),
        auto_now=True,
        db_index=True,
        help_text=_("Timestamp when the record was last updated")
    )

    class Meta:
        abstract = True
        ordering = ['-created_at']
        verbose_name = _('Time-Stamped Model')
        verbose_name_plural = _('Time-Stamped Models')

class OrganizationOwnedModel(TimeStampedModel):
    """
    Abstract model enforcing multi-tenancy through organization association.
    All child models will require an organization relationship with database constraints.
    """
    organization = models.ForeignKey(
        'organizations.Organization',
        on_delete=models.CASCADE,
        verbose_name=_('organization'),
        help_text=_("Organization that owns this record"),
        related_name="%(class)s_set"
    )

    class Meta:
        abstract = True
        constraints = [
            models.CheckConstraint(
                check=models.Q(organization__isnull=False),
                name='organization_required'
            )
        ]
        verbose_name = _('Organization-Owned Model')
        verbose_name_plural = _('Organization-Owned Models')

class AuditableModel(TimeStampedModel):
    """
    Abstract model tracking user responsible for creation/modification.
    Requires middleware to capture current user (to be implemented later).
    """
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='%(class)s_created',
        verbose_name=_('created by'),
        help_text=_("User who created this record")
    )
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='%(class)s_updated',
        verbose_name=_('updated by'),
        help_text=_("User who last modified this record")
    )

    class Meta:
        abstract = True
        constraints = [
            models.CheckConstraint(
                check=models.Q(created_by__isnull=False) | models.Q(updated_by__isnull=False),
                name='audit_trail_required'
            )
        ]
        verbose_name = _('Auditable Model')
        verbose_name_plural = _('Auditable Models')

    def save(self, *args, **kwargs):
        """
        Override save method to automatically capture current user.
        Note: Requires implementation of CurrentUserMiddleware
        """
        try:
            from apps.core.middleware import get_current_user
            user = get_current_user()
            if user and user.is_authenticated:
                if not self.pk:
                    self.created_by = user
                self.updated_by = user
        except ImportError:
            pass  # Handle middleware not yet implemented

        super().save(*args, **kwargs)

class TenantAuditableModel(AuditableModel, OrganizationOwnedModel):
    """
    Composite abstract model combining multi-tenancy and auditing.
    Use for models requiring both organization association and user tracking.
    """
    class Meta:
        abstract = True
        verbose_name = _('Tenant-Auditable Model')
        verbose_name_plural = _('Tenant-Auditable Models')

class SoftDeletionModel(models.Model):
    """
    Abstract model providing soft-delete capability.
    Use for models requiring logical deletion instead of physical removal.
    """
    deleted_at = models.DateTimeField(
        _('deleted at'),
        null=True,
        blank=True,
        editable=False,
        help_text=_("Timestamp when the record was soft-deleted")
    )

    class Meta:
        abstract = True
        verbose_name = _('Soft-Deletion Model')
        verbose_name_plural = _('Soft-Deletion Models')

    def delete(self, *args, **kwargs):
        """
        Override delete to perform soft deletion.
        Use force_delete() for physical deletion.
        """
        self.deleted_at = models.DateTimeField(auto_now_add=True)
        self.save()

    def force_delete(self, *args, **kwargs):
        """
        Perform physical deletion of the record.
        """
        super().delete(*args, **kwargs)