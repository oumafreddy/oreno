# apps/audit/signals.py

from django.db.models.signals import (
    post_save, pre_save, post_delete,
    m2m_changed
)
from django.dispatch import receiver
from django.utils.translation import gettext_lazy as _
from django.contrib.contenttypes.models import ContentType
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings

from core.mixins.state import DRAFT, PENDING, APPROVED, REJECTED
from .models import AuditWorkplan, Engagement, Issue, Approval
from .tasks import (
    send_approval_notification,
    process_approval_chain,
    update_related_states
)

# ─── WORKPLAN SIGNALS ────────────────────────────────────────────────────────
@receiver(pre_save, sender=AuditWorkplan)
def workplan_pre_save(sender, instance, **kwargs):
    """Handle pre-save operations for AuditWorkplan."""
    if not instance.pk:  # New instance
        instance.state = 'draft'

@receiver(post_save, sender=AuditWorkplan)
def workplan_post_save(sender, instance, created, **kwargs):
    """Handle post-save operations for AuditWorkplan."""
    if created:
        # Additional setup for new workplans
        pass

# ─── ENGAGEMENT SIGNALS ──────────────────────────────────────────────────────
@receiver(pre_save, sender=Engagement)
def engagement_pre_save(sender, instance, **kwargs):
    """Handle pre-save operations for Engagement."""
    if not instance.pk:  # New instance
        instance.state = 'draft'

@receiver(post_save, sender=Engagement)
def engagement_post_save(sender, instance, created, **kwargs):
    """Handle post-save operations for Engagement."""
    if created:
        # Additional setup for new engagements
        pass

# ─── ISSUE SIGNALS ──────────────────────────────────────────────────────────
@receiver(pre_save, sender=Issue)
def issue_pre_save(sender, instance, **kwargs):
    """Handle pre-save operations for Issue."""
    if not instance.pk:  # New instance
        instance.issue_status = 'open'
        instance.remediation_status = 'open'

@receiver(post_save, sender=Issue)
def issue_post_save(sender, instance, created, **kwargs):
    """Handle post-save operations for Issue."""
    if created:
        # Additional setup for new issues
        pass

# ─── APPROVAL SIGNALS ────────────────────────────────────────────────────────
@receiver(pre_save, sender=Approval)
def approval_pre_save(sender, instance, **kwargs):
    """Handle pre-save operations for Approval."""
    if not instance.pk:  # New instance
        instance.status = 'pending'

@receiver(post_save, sender=Approval)
def approval_post_save(sender, instance, created, **kwargs):
    """Handle post-save operations for Approval."""
    if created:
        # Additional setup for new approvals
        pass

# ─── M2M SIGNALS ────────────────────────────────────────────────────────────
@receiver(m2m_changed, sender=AuditWorkplan.engagements)
def workplan_engagements_changed(sender, instance, action, **kwargs):
    """
    Handle workplan-engagement relationship changes:
    - Validate engagement organization
    - Update related states
    """
    if action == 'pre_add':
        # Validate that all engagements belong to the same organization
        for engagement in kwargs['model'].objects.filter(pk__in=kwargs['pk_set']):
            if engagement.organization != instance.organization:
                raise ValueError(_("Cannot add engagement from different organization"))
    
    elif action == 'post_add':
        # Update engagement states when added to approved workplan
        if instance.state == APPROVED:
            update_related_states.delay(
                'Engagement',
                {'pk__in': kwargs['pk_set']},
                'state',
                PENDING
            )