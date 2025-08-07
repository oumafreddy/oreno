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
from django.db import transaction

from core.mixins.state import DRAFT, PENDING, APPROVED, REJECTED
from .models import AuditWorkplan, Engagement, Issue, Approval
from .tasks import (
    send_approval_notification,
    process_approval_chain,
    update_related_states,
    process_issue_working_paper_upload
)
from .models.note import Note, Notification
from .models.issue_working_paper import IssueWorkingPaper
from .models.risk import Risk
from .models.followupaction import FollowUpAction
from .models.issueretest import IssueRetest
from .models.recommendation import Recommendation
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

# ─── RISK SIGNALS ───────────────────────────────────────────────────────────
@receiver(pre_save, sender=Risk)
def risk_pre_save(sender, instance, **kwargs):
    """Handle pre-save operations for Risk. Set default status if new and track status changes."""
    if not instance.pk:  # New instance
        # Default status is handled in the model's save method
        pass
    else:
        # For existing instances, track status changes for notification purposes
        try:
            old_instance = Risk.objects.get(pk=instance.pk)
            if old_instance.status != instance.status:
                # Store old status for use in post_save
                instance._old_status = old_instance.status
        except Risk.DoesNotExist:
            pass

    if not instance.status:
        instance.status = 'identified'

@receiver(post_save, sender=Risk)
def risk_post_save(sender, instance, created, **kwargs):
    """Handle post-save operations for Risk."""
    status_changed = False  # Always define this variable for robust logic

    if created:
        # Log creation
        user = getattr(instance, 'created_by', None) or getattr(instance, 'last_modified_by', None)
        log_change(instance, 'create', user=user)
        # Notify when a new risk is created
        if instance.objective and instance.objective.engagement:
            engagement_owner = instance.objective.engagement.assigned_to
            if engagement_owner and engagement_owner.email:
                risk_level = instance.risk_level
                # Create context for email template
                context = {
                    'risk': instance,
                    'recipient': engagement_owner,
                    'site_name': settings.SITE_NAME if hasattr(settings, 'SITE_NAME') else 'Audit Management System',
                    'risk_url': f"{settings.BASE_URL}/audit/risks/{instance.id}/" if hasattr(settings, 'BASE_URL') else '',
                    'last_modified_by': getattr(instance, 'last_modified_by', None) or getattr(instance, 'updated_by', None) or getattr(instance, 'created_by', None) or 'System',
                }
                # Render HTML email
                html_message = render_to_string('audit/emails/risk_submitted.html', context)
                # Plain text fallback
                plain_message = f"A new {risk_level} risk has been identified in engagement '{instance.objective.engagement.title}'"
                transaction.on_commit(lambda: send_mail(
                    subject=f"New {risk_level} Risk Created: {instance.title}",
                    message=plain_message,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[engagement_owner.email],
                    fail_silently=True,
                    html_message=html_message
                ))
    else:
        # For existing instances, handle status changes
        status_changed = hasattr(instance, '_old_status') and instance._old_status != instance.status
        if status_changed:
            # Log status change
            user = getattr(instance, 'last_modified_by', None)
            log_change(instance, 'update', user=user)
    # Notify assigned person if applicable
    if instance.assigned_to and instance.assigned_to.email:
        # Notify if risk is newly created or status has changed or newly assigned
        if created or status_changed or (not created and hasattr(instance, '_old_assigned_to') and instance._old_assigned_to != instance.assigned_to):
            status_display = instance.get_status_display() if hasattr(instance, 'get_status_display') else instance.status
            risk_level = instance.risk_level
            subject = f"Risk Assignment: {instance.title} ({status_display})"
            if status_changed and not created:
                subject = f"Risk Status Change: {instance.title} - {status_display}"
            # Create context for email template
            context = {
                'risk': instance,
                'recipient': instance.assigned_to,
                'site_name': settings.SITE_NAME if hasattr(settings, 'SITE_NAME') else 'Audit Management System',
                'risk_url': f"{settings.BASE_URL}/audit/risks/{instance.id}/" if hasattr(settings, 'BASE_URL') else '',
                'last_modified_by': getattr(instance, 'last_modified_by', None) or getattr(instance, 'updated_by', None) or getattr(instance, 'created_by', None) or 'System',
            }
            # Select appropriate template based on status
            template_name = 'audit/emails/risk_assigned.html'
            if status_changed and not created:
                if instance.status == 'approved':
                    template_name = 'audit/emails/risk_approved.html'
                elif instance.status == 'rejected':
                    template_name = 'audit/emails/risk_rejected.html'
            # Render HTML email
            html_message = render_to_string(template_name, context)
            # Plain text fallback
            plain_message = f"{'You have been assigned to' if created or not status_changed else 'Status change for'} the risk '{instance.title}'"
            transaction.on_commit(lambda: send_mail(
                subject=subject,
                message=plain_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[instance.assigned_to.email],
                fail_silently=True,
                html_message=html_message
            ))
            # Create in-app notification
            Notification.objects.create(
                user=instance.assigned_to,
                message=f"{'You have been assigned to' if created or not status_changed else 'Status change for'} the risk '{instance.title}' ({status_display}).",
                notification_type='risk_assignment' if created or not status_changed else 'risk_status_change',
                organization=instance.organization
            )

# ─── FOLLOW-UP ACTION SIGNALS ───────────────────────────────────────────
@receiver(pre_save, sender=FollowUpAction)
def followup_action_pre_save(sender, instance, **kwargs):
    """Handle pre-save operations for FollowUpAction."""
    if not instance.pk:  # New instance
        # Default values are handled in model save method
        pass
    else:
        # For existing instances, track status changes for notification purposes
        try:
            old_instance = FollowUpAction.objects.get(pk=instance.pk)
            if old_instance.status != instance.status:
                # Store old status for use in post_save
                instance._old_status = old_instance.status
            if old_instance.assigned_to != instance.assigned_to:
                instance._old_assigned_to = old_instance.assigned_to
        except FollowUpAction.DoesNotExist:
            pass

@receiver(post_save, sender=FollowUpAction)
def followup_action_post_save(sender, instance, created, **kwargs):
    """Handle post-save operations for FollowUpAction."""
    if created:
        # Log creation
        user = getattr(instance, 'created_by', None) or getattr(instance, 'last_modified_by', None)
        log_change(instance, 'create', user=user)
        
        # Create notification for related issue owner if available
        if instance.issue and instance.issue.issue_owner:
            Notification.objects.create(
                user=instance.issue.issue_owner,
                message=f"New follow-up action created for issue {instance.issue.code}: {instance.title}",
                notification_type='followup_created',
                organization=instance.organization
            )
    else:
        # For existing instances, handle status changes
        status_changed = hasattr(instance, '_old_status') and instance._old_status != instance.status
        
        if status_changed:
            # Log status change
            user = getattr(instance, 'last_modified_by', None)
            log_change(instance, 'update', user=user)
            
            # If status changed to completed, notify the issue owner
            if instance.status == 'completed' and instance.issue and instance.issue.issue_owner:
                # Create context for email template
                context = {
                    'action': instance,
                    'recipient': instance.issue.issue_owner,
                    'site_name': settings.SITE_NAME if hasattr(settings, 'SITE_NAME') else 'Audit Management System',
                    'action_url': f"{settings.BASE_URL}/audit/followup-actions/{instance.id}/" if hasattr(settings, 'BASE_URL') else '',
                    'last_modified_by': getattr(instance, 'last_modified_by', None) or getattr(instance, 'updated_by', None) or getattr(instance, 'created_by', None) or 'System',
                }
                
                # Render HTML email
                html_message = render_to_string('audit/emails/followup_action_completed.html', context)
                
                # Plain text fallback
                plain_message = f"A follow-up action for issue {instance.issue.code} has been marked as completed."
                
                send_mail(
                    subject=f"Follow-up Action Completed: {instance.title}",
                    message=plain_message,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[instance.issue.issue_owner.email],
                    fail_silently=True,
                    html_message=html_message
                )
                
                # Create in-app notification
                Notification.objects.create(
                    user=instance.issue.issue_owner,
                    message=f"Follow-up action '{instance.title}' for issue {instance.issue.code} has been completed.",
                    notification_type='followup_completed',
                    organization=instance.organization
                )
    
    # Notify assigned person if applicable
    if instance.assigned_to and instance.assigned_to.email:
        # Notify if action is newly created or newly assigned
        if created or (hasattr(instance, '_old_assigned_to') and 
                      instance._old_assigned_to != instance.assigned_to):
            status_display = instance.get_status_display()
            
            # Create context for email template
            context = {
                'action': instance,
                'recipient': instance.assigned_to,
                'site_name': settings.SITE_NAME if hasattr(settings, 'SITE_NAME') else 'Audit Management System',
                'action_url': f"{settings.BASE_URL}/audit/followup-actions/{instance.id}/" if hasattr(settings, 'BASE_URL') else '',
                'last_modified_by': getattr(instance, 'last_modified_by', None) or getattr(instance, 'updated_by', None) or getattr(instance, 'created_by', None) or 'System',
            }
            
            # Render HTML email
            html_message = render_to_string('audit/emails/followup_action_assigned.html', context)
            
            # Plain text fallback
            plain_message = f"You have been assigned a follow-up action: {instance.title}"
            
            send_mail(
                subject=f"Follow-up Action Assignment: {instance.title}",
                message=plain_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[instance.assigned_to.email],
                fail_silently=True,
                html_message=html_message
            )
            
            # Create in-app notification
            Notification.objects.create(
                user=instance.assigned_to,
                message=f"You have been assigned the follow-up action: {instance.title}",
                notification_type='followup_assignment',
                organization=instance.organization
            )

# ─── ISSUE RETEST SIGNALS ────────────────────────────────────────────
@receiver(pre_save, sender=IssueRetest)
def issue_retest_pre_save(sender, instance, **kwargs):
    """Handle pre-save operations for IssueRetest."""
    if not instance.pk:  # New instance
        # Default values are handled in model save method
        pass
    else:
        # For existing instances, track result changes for notification purposes
        try:
            old_instance = IssueRetest.objects.get(pk=instance.pk)
            if old_instance.result != instance.result:
                # Store old result for use in post_save
                instance._old_result = old_instance.result
        except IssueRetest.DoesNotExist:
            pass

@receiver(post_save, sender=IssueRetest)
def issue_retest_post_save(sender, instance, created, **kwargs):
    """Handle post-save operations for IssueRetest."""
    if created:
        # Log creation
        user = getattr(instance, 'created_by', None) or getattr(instance, 'last_modified_by', None)
        log_change(instance, 'create', user=user)
        
        # Notify issue owner of scheduled retest
        if instance.issue and instance.issue.issue_owner and instance.issue.issue_owner.email:
            # Create context for email template
            context = {
                'retest': instance,
                'issue': instance.issue,
                'recipient': instance.issue.issue_owner,
                'site_name': settings.SITE_NAME if hasattr(settings, 'SITE_NAME') else 'Audit Management System',
                'retest_url': f"{settings.BASE_URL}/audit/issue-retests/{instance.id}/" if hasattr(settings, 'BASE_URL') else '',
                'last_modified_by': getattr(instance, 'last_modified_by', None) or getattr(instance, 'updated_by', None) or getattr(instance, 'created_by', None) or 'System',
            }
            
            # Render HTML email
            html_message = render_to_string('audit/emails/issue_retest_scheduled.html', context)
            
            # Plain text fallback
            plain_message = f"A retest has been scheduled for issue {instance.issue.code}"
            
            send_mail(
                subject=f"Retest Scheduled for Issue: {instance.issue.code}",
                message=plain_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[instance.issue.issue_owner.email],
                fail_silently=True,
                html_message=html_message
            )
    else:
        # For existing instances, handle result changes
        result_changed = hasattr(instance, '_old_result') and instance._old_result != instance.result
        
        if result_changed:
            # Log result change
            user = getattr(instance, 'last_modified_by', None)
            log_change(instance, 'update', user=user)
            
            # Notify issue owner of test results
            if instance.issue and instance.issue.issue_owner and instance.issue.issue_owner.email:
                result_display = instance.get_result_display() if hasattr(instance, 'get_result_display') else instance.result
                
                # Create context for email template
                context = {
                    'retest': instance,
                    'issue': instance.issue,
                    'recipient': instance.issue.issue_owner,
                    'result_display': result_display,
                    'site_name': settings.SITE_NAME if hasattr(settings, 'SITE_NAME') else 'Audit Management System',
                    'retest_url': f"{settings.BASE_URL}/audit/issue-retests/{instance.id}/" if hasattr(settings, 'BASE_URL') else '',
                    'last_modified_by': getattr(instance, 'last_modified_by', None) or getattr(instance, 'updated_by', None) or getattr(instance, 'created_by', None) or 'System',
                }
                
                # Render HTML email
                html_message = render_to_string('audit/emails/issue_retest_result.html', context)
                
                # Plain text fallback
                plain_message = f"A retest for issue {instance.issue.code} has been completed with result: {result_display}"
                
                send_mail(
                    subject=f"Retest Results for Issue: {instance.issue.code} - {result_display}",
                    message=plain_message,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[instance.issue.issue_owner.email],
                    fail_silently=True,
                    html_message=html_message
                )
                
                # Create in-app notification
                Notification.objects.create(
                    user=instance.issue.issue_owner,
                    message=f"Retest for issue {instance.issue.code} completed with result: {result_display}",
                    notification_type='retest_completed',
                    organization=instance.organization
                )

# ─── RECOMMENDATION SIGNALS ─────────────────────────────────────────
@receiver(pre_save, sender=Recommendation)
def recommendation_pre_save(sender, instance, **kwargs):
    """Handle pre-save operations for Recommendation."""
    if not instance.pk:  # New instance
        # Default values are handled in model save method
        pass
    else:
        # For existing instances, track implementation status changes for notification purposes
        try:
            old_instance = Recommendation.objects.get(pk=instance.pk)
            if old_instance.implementation_status != instance.implementation_status:
                # Store old status for use in post_save
                instance._old_implementation_status = old_instance.implementation_status
            if old_instance.assigned_to != instance.assigned_to:
                instance._old_assigned_to = old_instance.assigned_to
        except Recommendation.DoesNotExist:
            pass

@receiver(post_save, sender=Recommendation)
def recommendation_post_save(sender, instance, created, **kwargs):
    """Handle post-save operations for Recommendation."""
    if created:
        # Log creation
        user = getattr(instance, 'created_by', None) or getattr(instance, 'last_modified_by', None)
        log_change(instance, 'create', user=user)
        
        # Notify issue owner of new recommendation
        if instance.issue and instance.issue.issue_owner and instance.issue.issue_owner.email:
            # Create context for email template
            context = {
                'recommendation': instance,
                'issue': instance.issue,
                'recipient': instance.issue.issue_owner,
                'site_name': settings.SITE_NAME if hasattr(settings, 'SITE_NAME') else 'Audit Management System',
                'recommendation_url': f"{settings.BASE_URL}/audit/recommendations/{instance.id}/" if hasattr(settings, 'BASE_URL') else '',
                'last_modified_by': getattr(instance, 'last_modified_by', None) or getattr(instance, 'updated_by', None) or getattr(instance, 'created_by', None) or 'System',
            }
            
            # Render HTML email
            html_message = render_to_string('audit/emails/recommendation_created.html', context)
            
            # Plain text fallback
            plain_message = f"A new recommendation has been created for issue {instance.issue.code}: {instance.title}"
            
            send_mail(
                subject=f"New Recommendation for Issue: {instance.issue.code}",
                message=plain_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[instance.issue.issue_owner.email],
                fail_silently=True,
                html_message=html_message
            )
            
            # Create in-app notification
            if instance.issue.issue_owner:
                Notification.objects.create(
                    user=instance.issue.issue_owner,
                    message=f"New recommendation created for issue {instance.issue.code}: {instance.title}",
                    notification_type='recommendation_created',
                    organization=instance.organization
                )
    else:
        # For existing instances, handle implementation status changes
        status_changed = hasattr(instance, '_old_implementation_status') and instance._old_implementation_status != instance.implementation_status
        
        if status_changed:
            # Log status change
            user = getattr(instance, 'last_modified_by', None)
            log_change(instance, 'update', user=user)
            
            # Notify issue owner of status change
            if instance.issue and instance.issue.issue_owner and instance.issue.issue_owner.email:
                status_display = instance.get_implementation_status_display() if hasattr(instance, 'get_implementation_status_display') else instance.implementation_status
                
                # Create context for email template
                context = {
                    'recommendation': instance,
                    'recipient': instance.issue.issue_owner,
                    'old_status_display': instance._old_implementation_status,
                    'site_name': settings.SITE_NAME if hasattr(settings, 'SITE_NAME') else 'Audit Management System',
                    'recommendation_url': f"{settings.BASE_URL}/audit/recommendations/{instance.id}/" if hasattr(settings, 'BASE_URL') else '',
                    'last_modified_by': getattr(instance, 'last_modified_by', None) or getattr(instance, 'updated_by', None) or getattr(instance, 'created_by', None) or 'System',
                }
                
                # Render HTML email
                html_message = render_to_string('audit/emails/recommendation_status_updated.html', context)
                
                # Plain text fallback
                plain_message = f"The status of recommendation '{instance.title}' has been updated to {status_display}"
                
                send_mail(
                    subject=f"Recommendation Status Update: {instance.title} - {status_display}",
                    message=plain_message,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[instance.issue.issue_owner.email],
                    fail_silently=True,
                    html_message=html_message
                )
                
                # Create in-app notification
                Notification.objects.create(
                    user=instance.issue.issue_owner,
                    message=f"Recommendation '{instance.title}' status updated to: {status_display}",
                    notification_type='recommendation_status_updated',
                    organization=instance.organization
                )
    
    # Notify assigned person if applicable
    if instance.assigned_to and instance.assigned_to.email:
        # Notify if recommendation is newly created or newly assigned
        if created or (hasattr(instance, '_old_assigned_to') and 
                       instance._old_assigned_to != instance.assigned_to):
            priority_display = instance.get_priority_display() if hasattr(instance, 'get_priority_display') else instance.priority
            status_display = instance.get_implementation_status_display() if hasattr(instance, 'get_implementation_status_display') else instance.implementation_status
            
            # Create context for email template
            context = {
                'recommendation': instance,
                'recipient': instance.assigned_to,
                'priority_display': priority_display,
                'status_display': status_display,
                'site_name': settings.SITE_NAME if hasattr(settings, 'SITE_NAME') else 'Audit Management System',
                'recommendation_url': f"{settings.BASE_URL}/audit/recommendations/{instance.id}/" if hasattr(settings, 'BASE_URL') else '',
                'last_modified_by': getattr(instance, 'last_modified_by', None) or getattr(instance, 'updated_by', None) or getattr(instance, 'created_by', None) or 'System',
            }
            
            # Render HTML email
            html_message = render_to_string('audit/emails/recommendation_assigned.html', context)
            
            # Plain text fallback
            plain_message = f"You have been assigned a recommendation to implement: {instance.title}"
            
            send_mail(
                subject=f"Recommendation Assignment: {instance.title} ({priority_display})",
                message=plain_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[instance.assigned_to.email],
                fail_silently=True,
                html_message=html_message
            )
            
            # Create in-app notification
            Notification.objects.create(
                user=instance.assigned_to,
                message=f"You have been assigned a {priority_display} priority recommendation: {instance.title}",
                notification_type='recommendation_assignment',
                organization=instance.organization
            )

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
        Notification.create_for_user(
            user=instance.assigned_to,
            message=f"You have been assigned a new {instance.get_note_type_display()} on {instance.content_object}.",
            notification_type=instance.note_type,
            note=instance
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
        Notification.create_for_user(
            user=instance.user,
            message=f"The note you assigned on {instance.content_object} has been marked as cleared by {instance.assigned_to}.",
            notification_type='note_cleared',
            note=instance
        )

@receiver(post_save, sender=Issue)
def log_issue_change(sender, instance, created, **kwargs):
    # Log creation or update of issues (could be to a log file, audit trail, etc.)
    pass

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