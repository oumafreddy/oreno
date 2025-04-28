# audits/tasks.py
from celery import shared_task
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.translation import gettext_lazy as _
from django.contrib.contenttypes.models import ContentType
from django.db import transaction
from django.conf import settings

from .models import AuditWorkplan, Engagement, Issue, Approval
from core.mixins.state import PENDING, APPROVED, REJECTED

# ─── NOTIFICATION TASKS ──────────────────────────────────────────────────────
@shared_task
def send_approval_notification(email, notification_type, object_id):
    """
    Send approval-related notifications via email.
    
    Args:
        email (str): Recipient email address
        notification_type (str): Type of notification (e.g., 'workplan_pending')
        object_id (int): ID of the related object
    """
    templates = {
        'workplan_pending': {
            'subject': _('Workplan Pending Approval'),
            'template': 'audit/emails/workplan_pending.txt'
        },
        'engagement_pending': {
            'subject': _('Engagement Pending Approval'),
            'template': 'audit/emails/engagement_pending.txt'
        }
    }
    
    if notification_type not in templates:
        return
    
    template = templates[notification_type]
    context = {
        'object': get_object_for_notification(notification_type, object_id),
        'site_name': settings.SITE_NAME
    }
    
    send_mail(
        template['subject'],
        render_to_string(template['template'], context),
        settings.DEFAULT_FROM_EMAIL,
        [email],
        fail_silently=True
    )

def get_object_for_notification(notification_type, object_id):
    """Helper function to get the appropriate object for notification context"""
    if notification_type == 'workplan_pending':
        return AuditWorkplan.objects.get(pk=object_id)
    elif notification_type == 'engagement_pending':
        return Engagement.objects.get(pk=object_id)
    return None

# ─── STATE UPDATE TASKS ──────────────────────────────────────────────────────
@shared_task
def update_related_states(model_name, filter_kwargs, field_name, new_value):
    """
    Update states of related objects asynchronously.
    
    Args:
        model_name (str): Name of the model to update
        filter_kwargs (dict): Filter criteria for objects to update
        field_name (str): Name of the field to update
        new_value: New value to set
    """
    model_map = {
        'Engagement': Engagement,
        'Issue': Issue
    }
    
    if model_name not in model_map:
        return
    
    model = model_map[model_name]
    with transaction.atomic():
        model.objects.filter(**filter_kwargs).update(**{field_name: new_value})

# ─── APPROVAL CHAIN TASKS ────────────────────────────────────────────────────
@shared_task
def process_approval_chain(approval_id):
    """
    Process the approval chain for an object.
    
    Args:
        approval_id (int): ID of the approval object
    """
    try:
        approval = Approval.objects.select_related(
            'content_type',
            'requester',
            'approver'
        ).get(pk=approval_id)
        
        content_object = approval.content_type.get_object_for_this_type(
            pk=approval.object_id
        )
        
        if approval.status == 'approved':
            # Update object state
            if hasattr(content_object, 'state'):
                content_object.state = APPROVED
                content_object.save()
            
            # Create next approval step if needed
            create_next_approval_step(content_object)
        
        elif approval.status == 'rejected':
            # Update object state
            if hasattr(content_object, 'state'):
                content_object.state = REJECTED
                content_object.save()
            
            # Notify requester
            send_mail(
                _('Approval Rejected'),
                render_to_string('audit/emails/approval_rejected.txt', {
                    'approval': approval,
                    'site_name': settings.SITE_NAME
                }),
                settings.DEFAULT_FROM_EMAIL,
                [approval.requester.email],
                fail_silently=True
            )
    
    except Approval.DoesNotExist:
        # Log error or handle as needed
        pass

def create_next_approval_step(content_object):
    """
    Create the next step in the approval chain if needed.
    
    Args:
        content_object: The object being approved
    """
    if hasattr(content_object, 'get_next_approvers'):
        next_approvers = content_object.get_next_approvers()
        if next_approvers:
            for approver in next_approvers:
                Approval.objects.create(
                    content_type=ContentType.objects.get_for_model(content_object),
                    object_id=content_object.pk,
                    organization=content_object.organization,
                    requester=content_object.created_by,
                    approver=approver
                )

# ─── BULK OPERATION TASKS ────────────────────────────────────────────────────
@shared_task
def bulk_update_workplan_states(workplan_ids, new_state):
    """
    Update states of multiple workplans asynchronously.
    
    Args:
        workplan_ids (list): List of workplan IDs to update
        new_state (str): New state to set
    """
    with transaction.atomic():
        AuditWorkplan.objects.filter(pk__in=workplan_ids).update(state=new_state)

@shared_task
def bulk_update_engagement_states(engagement_ids, new_state):
    """
    Update states of multiple engagements asynchronously.
    
    Args:
        engagement_ids (list): List of engagement IDs to update
        new_state (str): New state to set
    """
    with transaction.atomic():
        Engagement.objects.filter(pk__in=engagement_ids).update(state=new_state)

# ─── CLEANUP TASKS ───────────────────────────────────────────────────────────
@shared_task
def cleanup_old_approvals(days=30):
    """
    Clean up old approval records.
    
    Args:
        days (int): Number of days after which to clean up approvals
    """
    from django.utils import timezone
    from datetime import timedelta
    
    cutoff_date = timezone.now() - timedelta(days=days)
    Approval.objects.filter(
        created_at__lt=cutoff_date,
        status__in=['approved', 'rejected']
    ).delete()

@shared_task
def archive_completed_engagements(days=90):
    """
    Archive completed engagements after a certain period.
    
    Args:
        days (int): Number of days after completion to archive
    """
    from django.utils import timezone
    from datetime import timedelta
    
    cutoff_date = timezone.now() - timedelta(days=days)
    Engagement.objects.filter(
        project_status='closed',
        updated_at__lt=cutoff_date
    ).update(is_archived=True)