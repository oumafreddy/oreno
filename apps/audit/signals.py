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
    update_related_states,
    process_issue_working_paper_upload
)
from .models.note import Note, Notification
from .models.procedureresult import ProcedureResult
from .models.issue_working_paper import IssueWorkingPaper
from core.signals import log_change

# ─── WORKPLAN SIGNALS ────────────────────────────────────────────────────────
# @receiver(pre_save, sender=AuditWorkplan)
# def workplan_pre_save(sender, instance, **kwargs):
#     if not instance.pk:  # New instance
#         # instance.state = 'draft'  # <-- Direct assignment forbidden by django-fsm. Let FSMField default handle this.
#         pass  # See django-fsm docs: https://github.com/viewflow/django-fsm#direct-state-modification-is-not-allowed

@receiver(post_save, sender=AuditWorkplan)
def workplan_post_save(sender, instance, created, **kwargs):
    """Handle post-save operations for AuditWorkplan."""
    if created:
        # Additional setup for new workplans
        pass

# ─── ENGAGEMENT SIGNALS ──────────────────────────────────────────────────────
# @receiver(pre_save, sender=Engagement)
# def engagement_pre_save(sender, instance, **kwargs):
#     if not instance.pk:  # New instance
#         # instance.state = 'draft'  # <-- Direct assignment forbidden by django-fsm. Let FSMField default handle this.
#         pass

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
# @receiver(pre_save, sender=Approval)
# def approval_pre_save(sender, instance, **kwargs):
#     if not instance.pk:  # New instance
#         # instance.status = 'pending'  # <-- If this is FSMField, do not assign directly. Let default handle.
#         pass

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
        # Update engagement approval status when added to approved workplan
        if instance.approval_status == APPROVED:
            update_related_states.delay(
                'Engagement',
                {'pk__in': kwargs['pk_set']},
                'approval_status',
                PENDING
            )

def send_notification(user, message):
    # Placeholder for notification logic (email, in-app, etc.)
    pass

@receiver(post_save, sender=Note)
def notify_note_assignment(sender, instance, created, **kwargs):
    # On creation, notify assigned_to for review, to-do, or review_request
    if created and instance.assigned_to and instance.status == 'open' and instance.note_type in ['review', 'todo', 'review_request']:
        send_mail(
            subject=f"New {instance.get_note_type_display()} Assigned",
            message=f"You have been assigned a new {instance.get_note_type_display()} on {instance.content_object}.\n\nContent: {instance.content}",
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[instance.assigned_to.email],
            fail_silently=True,
        )
        # In-app notification
        Notification.objects.create(
            user=instance.assigned_to,
            note=instance,
            message=f"You have been assigned a new {instance.get_note_type_display()} on {instance.content_object}.",
            notification_type=instance.note_type
        )
    # On status change to 'cleared', notify supervisor (user field)
    elif not created and instance.status == 'cleared' and instance.user:
        send_mail(
            subject=f"Review Note/To-Do Cleared: {instance.note_type.title()}",
            message=f"The note you assigned on {instance.content_object} has been marked as cleared by {instance.assigned_to}.",
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[instance.user.email],
            fail_silently=True,
        )
        # In-app notification
        Notification.objects.create(
            user=instance.user,
            note=instance,
            message=f"The note you assigned on {instance.content_object} has been marked as cleared by {instance.assigned_to}.",
            notification_type='note_cleared'
        )

@receiver(post_save, sender=Issue)
def log_issue_change(sender, instance, created, **kwargs):
    # Log creation or update of issues (could be to a log file, audit trail, etc.)
    pass

@receiver(post_save, sender=ProcedureResult)
def auto_close_procedure(sender, instance, **kwargs):
    # Example: if all results for a procedure are 'operating_effectively', mark procedure as complete
    pass

# ─── ISSUE WORKING PAPER SIGNALS ─────────────────────────────────────────────
@receiver(post_save, sender=IssueWorkingPaper)
def issue_working_paper_post_save(sender, instance, created, **kwargs):
    # Log creation or update of working papers (could be to a log file, audit trail, etc.)
    user = getattr(instance, 'created_by', None)
    action = 'create' if created else 'update'
    log_change(instance, action, user=user)
    # Trigger async processing (virus scan, notification, etc.)
    process_issue_working_paper_upload.delay(instance.pk)
    # Notify issue owner if available
    issue = getattr(instance, 'issue', None)
    if issue and issue.issue_owner and issue.issue_owner.email:
        send_mail(
            subject=f"New Working Paper Uploaded for Issue: {issue.issue_title}",
            message=f"A new working paper has been uploaded for the issue '{issue.issue_title}'.\n\nDescription: {instance.description}",
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[issue.issue_owner.email],
            fail_silently=True,
        )

@receiver(post_delete, sender=IssueWorkingPaper)
def issue_working_paper_post_delete(sender, instance, **kwargs):
    user = getattr(instance, 'created_by', None)
    log_change(instance, 'delete', user=user)
    # Optionally notify issue owner of deletion
    issue = getattr(instance, 'issue', None)
    if issue and issue.issue_owner and issue.issue_owner.email:
        send_mail(
            subject=f"Working Paper Deleted for Issue: {issue.issue_title}",
            message=f"A working paper has been deleted for the issue '{issue.issue_title}'.\n\nDescription: {instance.description}",
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[issue.issue_owner.email],
            fail_silently=True,
        )