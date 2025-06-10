# audits/tasks.py
from celery import shared_task
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.translation import gettext_lazy as _
from django.contrib.contenttypes.models import ContentType
from django.db import transaction
from django.conf import settings

from .models import AuditWorkplan, Engagement, Issue, Approval, Risk, Objective
from core.mixins.state import PENDING, APPROVED, REJECTED
from .models.note import Note
from .models.issue_working_paper import IssueWorkingPaper
from core.models.validators import validate_file_virus
from core.signals import log_change
from .email_utils import send_risk_status_notification, send_risk_assignment_notification, send_risk_approval_notification

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
            # Update object approval status
            if hasattr(content_object, 'approval_status'):
                content_object.approval_status = APPROVED
                content_object.save()
            
            # Create next approval step if needed
            create_next_approval_step(content_object)
        
        elif approval.status == 'rejected':
            # Update object approval status
            if hasattr(content_object, 'approval_status'):
                content_object.approval_status = REJECTED
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
    Update approval status of multiple workplans asynchronously.
    
    Args:
        workplan_ids (list): List of workplan IDs to update
        new_state (str): New state to set
    """
    with transaction.atomic():
        AuditWorkplan.objects.filter(pk__in=workplan_ids).update(approval_status=new_state)

@shared_task
def bulk_update_engagement_states(engagement_ids, new_state):
    """
    Update approval status of multiple engagements asynchronously.
    
    Args:
        engagement_ids (list): List of engagement IDs to update
        new_state (str): New state to set
    """
    with transaction.atomic():
        Engagement.objects.filter(pk__in=engagement_ids).update(approval_status=new_state)

# ─── RISK MANAGEMENT TASKS ───────────────────────────────────────────────────
@shared_task
def recalculate_risk_scores(risk_ids):
    """
    Recalculate risk scores for multiple risks asynchronously.
    This is used after control effectiveness changes or when updating multiple risks.
    
    Args:
        risk_ids (list): List of risk IDs to recalculate scores for
    """
    with transaction.atomic():
        risks = Risk.objects.filter(id__in=risk_ids)
        
        for risk in risks:
            # Log original values for audit trail
            old_inherent = risk.inherent_risk_score
            old_residual = risk.residual_risk_score
            old_status = risk.status
            
            # Use save() method which contains the calculation logic
            risk.save()
            
            # Log changes if scores changed
            if (old_inherent != risk.inherent_risk_score or 
                old_residual != risk.residual_risk_score or 
                old_status != risk.status):
                log_change(
                    risk, 
                    'update',
                    changes={
                        'inherent_risk_score': (old_inherent, risk.inherent_risk_score),
                        'residual_risk_score': (old_residual, risk.residual_risk_score),
                        'status': (old_status, risk.status)
                    }
                )
                
                # Send notification if status changed
                if old_status != risk.status:
                    send_risk_status_notification(risk, old_status, risk.status)

@shared_task
def process_risk_approval(risk_id, approval_status, approver_id=None):
    """
    Process risk approval asynchronously.
    Updates risk status and sends notifications based on approval outcome.
    
    Args:
        risk_id (int): ID of the risk to process
        approval_status (str): New approval status (approved/rejected)
        approver_id (int): ID of the user who approved/rejected
    """
    try:
        risk = Risk.objects.get(pk=risk_id)
        
        # Update the risk based on approval status
        if approval_status == APPROVED:
            if risk.status == 'assessed':
                risk.status = 'mitigated'
            
            # Send approval notification
            send_risk_approval_notification(risk, 'approved')
            
        elif approval_status == REJECTED:
            # Send rejection notification
            send_risk_approval_notification(risk, 'rejected')
        
        # Save the risk with updated status
        risk.save()
        
        # Log the approval action
        from django.contrib.auth import get_user_model
        User = get_user_model()
        
        if approver_id:
            try:
                approver = User.objects.get(pk=approver_id)
                log_change(risk, 'update', 
                           changes={'approval_status': approval_status},
                           user=approver)
            except User.DoesNotExist:
                log_change(risk, 'update', 
                           changes={'approval_status': approval_status})
    
    except Risk.DoesNotExist:
        pass

@shared_task
def bulk_update_risk_states(risk_ids, new_state):
    """
    Update status of multiple risks asynchronously.
    
    Args:
        risk_ids (list): List of risk IDs to update
        new_state (str): New state to set
    """
    valid_states = ['identified', 'assessed', 'mitigated', 'accepted', 'transferred', 'closed']
    
    if new_state not in valid_states:
        return
    
    with transaction.atomic():
        risks = Risk.objects.filter(pk__in=risk_ids)
        for risk in risks:
            old_state = risk.status
            risk.status = new_state
            risk.save()
            
            # Send notification about status change
            if old_state != new_state:
                send_risk_status_notification(risk, old_state, new_state)


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

@shared_task
def send_note_notification(note_id):
    note = Note.objects.get(pk=note_id)
    if note.user and note.user.email:
        send_mail(
            subject="You have a new review note",
            message=note.content,
            from_email="noreply@yourdomain.com",
            recipient_list=[note.user.email]
        )

# ─── ISSUE WORKING PAPER TASKS ───────────────────────────────────────────────
@shared_task
def process_issue_working_paper_upload(issue_working_paper_id):
    """
    Async processing of uploaded working papers: virus scan, audit log, notification.
    """
    try:
        working_paper = IssueWorkingPaper.objects.get(pk=issue_working_paper_id)
        file = working_paper.file
        user = getattr(working_paper, 'created_by', None)
        # Virus scan
        try:
            validate_file_virus(file)
            scan_result = 'clean'
        except Exception as e:
            scan_result = f'virus_detected: {str(e)}'
            # Log virus detection
            log_change(working_paper, 'update', changes={'virus_scan': scan_result}, user=user)
            # Optionally notify admin or security team
            return
        # Log successful scan
        log_change(working_paper, 'update', changes={'virus_scan': scan_result}, user=user)
        # Notify issue owner
        issue = getattr(working_paper, 'issue', None)
        if issue and issue.issue_owner and issue.issue_owner.email:
            send_mail(
                subject=f"Working Paper Virus Scan Result for Issue: {issue.issue_title}",
                message=f"The uploaded working paper for issue '{issue.issue_title}' has been scanned and is {scan_result}.",
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[issue.issue_owner.email],
                fail_silently=True,
            )
    except IssueWorkingPaper.DoesNotExist:
        pass