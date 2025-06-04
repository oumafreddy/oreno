from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
import logging

logger = logging.getLogger(__name__)

# All email notification functions moved here

def send_workplan_approval_notification(workplan, status, request):
    """
    Send email notification for workplan approval status changes.
    Implementation moved from utils.py
    """
    # Use settings directly instead of Site model
    site_name = getattr(settings, 'SITE_NAME', "Audit Management System")
        
    recipients = []
    subject = ""
    template_name = ""
    
    if status == "submitted":
        if workplan.organization.approval_group and workplan.organization.approval_group.user_set.exists():
            recipients = workplan.organization.approval_group.user_set.values_list('email', flat=True)
            subject = _('Audit Workplan Submitted for Approval')
            template_name = 'audit/emails/workplan_submitted.html'
    elif status == "approved":
        if workplan.created_by and workplan.created_by.email:
            recipients = [workplan.created_by.email]
            subject = _('Audit Workplan Approved')
            template_name = 'audit/emails/workplan_approved.html'
    elif status == "rejected":
        if workplan.created_by and workplan.created_by.email:
            recipients = [workplan.created_by.email]
            subject = _('Audit Workplan Needs Revision')
            template_name = 'audit/emails/workplan_rejected.html'
    
    if not recipients or not subject or not template_name:
        return
    
    context = {
        'workplan': workplan,
        'status': status,
        'site_name': site_name,
        'site_domain': settings.SITE_DOMAIN,
    }
    
    try:
        html_message = render_to_string(template_name, context)
        send_mail(
            subject=subject,
            message="",  # Plain text version - we're using HTML email
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=recipients,
            fail_silently=True,
            html_message=html_message
        )
        logger.info(f"Workplan approval notification sent for {workplan.id} with status {status}")
    except Exception as e:
        logger.error(f"Failed to send workplan approval notification: {e}")

def send_engagement_approval_notification(engagement, status, request):
    """
    Send email notification for engagement approval status changes.
    Implementation moved from utils.py
    """
    # Use settings directly instead of Site model
    site_name = getattr(settings, 'SITE_NAME', "Audit Management System")
        
    recipients = []
    subject = ""
    template_name = ""
    
    if status == "submitted":
        if engagement.organization.approval_group and engagement.organization.approval_group.user_set.exists():
            recipients = engagement.organization.approval_group.user_set.values_list('email', flat=True)
            subject = _('Audit Engagement Submitted for Approval')
            template_name = 'audit/emails/engagement_submitted.html'
    elif status == "approved":
        if engagement.created_by and engagement.created_by.email:
            recipients = [engagement.created_by.email]
            subject = _('Audit Engagement Approved')
            template_name = 'audit/emails/engagement_approved.html'
    elif status == "rejected":
        if engagement.created_by and engagement.created_by.email:
            recipients = [engagement.created_by.email]
            subject = _('Audit Engagement Needs Revision')
            template_name = 'audit/emails/engagement_rejected.html'
    
    if not recipients or not subject or not template_name:
        return
    
    context = {
        'engagement': engagement,
        'status': status,
        'site_name': site_name,
        'site_domain': settings.SITE_DOMAIN,
    }
    
    try:
        html_message = render_to_string(template_name, context)
        send_mail(
            subject=subject,
            message="",  # Plain text version - we're using HTML email
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=recipients,
            fail_silently=True,
            html_message=html_message
        )
        logger.info(f"Engagement approval notification sent for {engagement.id} with status {status}")
    except Exception as e:
        logger.error(f"Failed to send engagement approval notification: {e}")

def send_risk_status_notification(risk, old_status, new_status, request=None):
    """
    Send email notification for risk status changes.
    Follows the same notification pattern as approvals but for risk status transitions.
    """
    # Use settings directly instead of Site model
    site_name = getattr(settings, 'SITE_NAME', "Audit Management System")
    
    # Only notify the risk owner and engagement lead
    recipients = []
    
    # The risk owner (creator) should be notified of status changes
    if risk.created_by and risk.created_by.email:
        recipients.append(risk.created_by.email)
    
    # The objective owner or engagement lead should also be notified
    if risk.objective and risk.objective.engagement:
        engagement = risk.objective.engagement
        if engagement.lead and engagement.lead.email and engagement.lead.email not in recipients:
            recipients.append(engagement.lead.email)
    
    if not recipients:
        return
    
    subject = _(f'Risk Status Changed: {risk.title}')
    template_name = 'audit/emails/risk_status_changed.html'
    
    context = {
        'risk': risk,
        'old_status': old_status,
        'new_status': new_status,
        'site_name': site_name,
        'site_domain': settings.SITE_DOMAIN,
    }
    
    try:
        html_message = render_to_string(template_name, context)
        send_mail(
            subject=subject,
            message="",  # Plain text version - we're using HTML email
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=recipients,
            fail_silently=True,
            html_message=html_message
        )
        logger.info(f"Risk status notification sent for {risk.id} from {old_status} to {new_status}")
    except Exception as e:
        logger.error(f"Failed to send risk status notification: {e}")


def send_risk_approval_notification(risk, status, request=None):
    """
    Send email notification for risk approval status changes.
    Similar to workplan and engagement approval notifications.
    """
    # Use settings directly instead of Site model
    site_name = getattr(settings, 'SITE_NAME', "Audit Management System")
        
    recipients = []
    subject = ""
    template_name = ""
    
    if status == "submitted":
        # For risk approval requests, notify the objective owner or engagement lead
        notify_list = []
        if risk.objective and risk.objective.engagement:
            engagement = risk.objective.engagement
            if engagement.lead and engagement.lead.email:
                notify_list.append(engagement.lead.email)
        
        if not notify_list and risk.organization.approval_group:
            notify_list = risk.organization.approval_group.user_set.values_list('email', flat=True)
        
        recipients = list(notify_list)
        subject = _(f'Risk Assessment Submitted for Approval: {risk.title}')
        template_name = 'audit/emails/risk_submitted.html'
    
    elif status == "approved":
        if risk.created_by and risk.created_by.email:
            recipients = [risk.created_by.email]
            subject = _(f'Risk Assessment Approved: {risk.title}')
            template_name = 'audit/emails/risk_approved.html'
    
    elif status == "rejected":
        if risk.created_by and risk.created_by.email:
            recipients = [risk.created_by.email]
            subject = _(f'Risk Assessment Needs Revision: {risk.title}')
            template_name = 'audit/emails/risk_rejected.html'
    
    if not recipients or not subject or not template_name:
        return
    
    context = {
        'risk': risk,
        'status': status,
        'site_name': site_name,
        'site_domain': settings.SITE_DOMAIN,
    }
    
    try:
        html_message = render_to_string(template_name, context)
        send_mail(
            subject=subject,
            message="",  # Plain text version - we're using HTML email
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=recipients,
            fail_silently=True,
            html_message=html_message
        )
        logger.info(f"Risk approval notification sent for {risk.id} with status {status}")
    except Exception as e:
        logger.error(f"Failed to send risk approval notification: {e}")


def send_risk_assignment_notification(risk, request=None):
    """
    Send notification when a risk is assigned to someone.
    """
    if not risk.assigned_to or not risk.assigned_to.email:
        return
        
    # Use settings directly instead of Site model
    site_name = getattr(settings, 'SITE_NAME', "Audit Management System")
    
    subject = _(f'Risk Assigned: {risk.title}')
    template_name = 'audit/emails/risk_assigned.html'
    
    context = {
        'risk': risk,
        'site_name': site_name,
        'site_domain': settings.SITE_DOMAIN,
    }
    
    try:
        html_message = render_to_string(template_name, context)
        send_mail(
            subject=subject,
            message="",  # Plain text version - we're using HTML email
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[risk.assigned_to.email],
            fail_silently=True,
            html_message=html_message
        )
        logger.info(f"Risk assignment notification sent for {risk.id} to {risk.assigned_to.email}")
    except Exception as e:
        logger.error(f"Failed to send risk assignment notification: {e}")
