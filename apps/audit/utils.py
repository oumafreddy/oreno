"""
Utility functions for the audit app.
"""
from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
import logging

logger = logging.getLogger(__name__)

def is_htmx_request(request):
    """
    Safely check if the request is an HTMX request.
    Handles possible attribute errors.
    """
    return request.headers.get('HX-Request') == 'true'


def send_approval_notification(approval, request=None):
    """
    Send an email notification to the approver about a new approval request.
    
    Args:
        approval: The Approval instance
        request: The HTTP request object (optional, for building absolute URLs)
    """
    context = build_approval_email_context(approval, request)
    
    subject = _("New approval request: {0}").format(str(approval.content_object))
    template = 'audit/emails/approval_request.html'
    
    _send_templated_email(
        subject=subject,
        template=template,
        context=context,
        recipient_email=approval.approver.email
    )


def send_approval_status_notification(approval, request=None):
    """
    Send an email notification to the requester about the status of their approval request.
    
    Args:
        approval: The Approval instance
        request: The HTTP request object (optional, for building absolute URLs)
    """
    context = build_approval_email_context(approval, request)
    
    if approval.status == 'approved':
        subject = _("Approval request approved: {0}").format(str(approval.content_object))
        template = 'audit/emails/approval_approved.html'
    else:
        subject = _("Approval request rejected: {0}").format(str(approval.content_object))
        template = 'audit/emails/approval_rejected.html'
    
    _send_templated_email(
        subject=subject,
        template=template,
        context=context,
        recipient_email=approval.requester.email
    )


def build_approval_email_context(approval, request=None):
    """
    Build the context dictionary for approval notification emails.
    
    Args:
        approval: The Approval instance
        request: The HTTP request object (optional, for building absolute URLs)
        
    Returns:
        A dictionary with the context for the email template
    """
    from .models import AuditWorkplan, Engagement
    
    # Get the content object
    content_object = approval.content_object
    organization = approval.organization
    
    # Get base URL for links in emails
    base_url = settings.BASE_URL if hasattr(settings, 'BASE_URL') else ''
    
    # If we have a request object, use it to build absolute URLs
    if request:
        base_url = request.build_absolute_uri('/').rstrip('/')
    
    # Build the approval detail URL
    approval_url = f"{base_url}{reverse('audit:approval-detail', kwargs={'pk': approval.pk})}"
    
    # Base context
    context = {
        'approval': approval,
        'content_object': content_object,
        'approver': approval.approver,
        'requester': approval.requester,
        'organization': organization,
        'approval_url': approval_url,
    }
    
    # Add specific context based on content object type
    if isinstance(content_object, AuditWorkplan):
        context['workplan'] = content_object
        context['workplan_url'] = f"{base_url}{reverse('audit:workplan-detail', kwargs={'pk': content_object.pk})}"
    elif isinstance(content_object, Engagement):
        context['engagement'] = content_object
        context['engagement_url'] = f"{base_url}{reverse('audit:engagement-detail', kwargs={'pk': content_object.pk})}"
    
    return context


def _send_templated_email(subject, template, context, recipient_email):
    """
    Send an email using a template.
    
    Args:
        subject: Email subject
        template: Path to the email template
        context: Context dictionary for the template
        recipient_email: Email address of the recipient
    """
    # Render the HTML message
    html_message = render_to_string(template, context)
    
    # Create a plain text version of the message
    # This is a simplified version of the HTML message
    plain_message = f"""
    {subject}
    
    Please view this message in an HTML-capable email client.
    """
    
    # Send the email
    from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', None)
    
    send_mail(
        subject=subject,
        message=plain_message,
        from_email=from_email,
        recipient_list=[recipient_email],
        html_message=html_message,
        fail_silently=False,
    )


def get_workplan_approvers(organization):
    """
    Get users who can approve workplans (Head of Unit and Admin roles).
    Workplans are submitted by Managers and approved by Head of Unit.
    
    Args:
        organization: The organization instance
        
    Returns:
        QuerySet of users with Head of Unit or Admin roles in the organization
    """
    from django.contrib.auth import get_user_model
    User = get_user_model()
    
    return User.objects.filter(
        organization=organization,
        role__in=['head_of_unit', 'admin']
    ).distinct()

def get_engagement_approvers(organization):
    """
    Get users who can approve engagements (Manager, Head of Unit, and Admin roles).
    Engagements are submitted by Staff and approved by Managers.
    
    Args:
        organization: The organization instance
        
    Returns:
        QuerySet of users with Manager, Head of Unit, or Admin roles in the organization
    """
    from django.contrib.auth import get_user_model
    User = get_user_model()
    
    return User.objects.filter(
        organization=organization,
        role__in=['manager', 'head_of_unit', 'admin']
    ).distinct()

def get_workplan_submitters(organization):
    """
    Get users who can submit workplans (Manager, Head of Unit, and Admin roles).
    
    Args:
        organization: The organization instance
        
    Returns:
        QuerySet of users with Manager, Head of Unit, or Admin roles in the organization
    """
    from django.contrib.auth import get_user_model
    User = get_user_model()
    
    return User.objects.filter(
        organization=organization,
        role__in=['manager', 'head_of_unit', 'admin']
    ).distinct()

def get_engagement_submitters(organization):
    """
    Get users who can submit engagements (Staff, Manager, Head of Unit, and Admin roles).
    
    Args:
        organization: The organization instance
        
    Returns:
        QuerySet of users with Staff, Manager, Head of Unit, or Admin roles in the organization
    """
    from django.contrib.auth import get_user_model
    User = get_user_model()
    
    return User.objects.filter(
        organization=organization,
        role__in=['staff', 'manager', 'head_of_unit', 'admin']
    ).distinct()

def send_workplan_approval_notification(workplan, status, request):
    """
    Send email notification for workplan approval status changes.
    
    Args:
        workplan: The AuditWorkplan instance
        status: The approval status ('submitted', 'approved', 'rejected')
        request: The HTTP request object
    """
    from django.contrib.auth import get_user_model
    User = get_user_model()
    
    # Determine appropriate email template and subject based on status
    if status == 'submitted':
        template = 'audit/emails/workplan_submitted.html'
        subject = f'Workplan Approval Request: {workplan.title}'
    elif status == 'approved':
        template = 'audit/emails/workplan_approved.html'
        subject = f'Workplan Approved: {workplan.title}'
    elif status == 'rejected':
        template = 'audit/emails/workplan_rejected.html'
        subject = f'Workplan Rejected: {workplan.title}'
    else:
        # Invalid status
        return False
    
    # Get base URL for links in emails
    base_url = settings.BASE_URL if hasattr(settings, 'BASE_URL') else ''
    
    # If we have a request object, use it to build absolute URLs
    if request:
        base_url = request.build_absolute_uri('/').rstrip('/')
    
    # Build the workplan detail URL
    workplan_url = f"{base_url}{reverse('audit:workplan-detail', kwargs={'pk': workplan.pk})}"
    
    context = {
        'workplan': workplan,
        'workplan_url': workplan_url,
        'organization': workplan.organization,
        'requester': request.user,
    }
    
    if status == 'submitted':
        # Notify approvers using the new approval hierarchy
        approvers = get_workplan_approvers(workplan.organization)
        
        if not approvers.exists():
            # Fallback: notify admins if no Head of Unit exists
            approvers = User.objects.filter(
                organization=workplan.organization,
                role='admin'
            )
        
        for approver in approvers:
            context['approver'] = approver
            _send_templated_email(
                subject=subject,
                template=template,
                context=context,
                recipient_email=approver.email
            )
            
    elif status == 'approved' or status == 'rejected':
        # Notify the submitter
        # Get the owner/creator of the workplan
        if hasattr(workplan, 'created_by') and workplan.created_by:
            context['requester'] = workplan.created_by
            
            # Get the last approval record for this workplan
            from .models import Approval
            from django.contrib.contenttypes.models import ContentType
            
            approval = Approval.objects.filter(
                content_type=ContentType.objects.get_for_model(workplan),
                object_id=workplan.pk,
                status=status
            ).order_by('-updated_at').first()
            
            if approval:
                context['approval'] = approval
                context['approver'] = approval.approver
            
            _send_templated_email(
                subject=subject,
                template=template,
                context=context,
                recipient_email=workplan.created_by.email
            )


def send_engagement_approval_notification(engagement, status, request):
    """
    Send email notification for engagement approval status changes.
    
    Args:
        engagement: The Engagement instance
        status: The approval status ('submitted', 'approved', 'rejected')
        request: The HTTP request object
    """
    from django.contrib.auth import get_user_model
    User = get_user_model()
    
    # Determine appropriate email template and subject based on status
    if status == 'submitted':
        template = 'audit/emails/engagement_submitted.html'
        subject = f'Engagement Approval Request: {engagement.title}'
    elif status == 'approved':
        template = 'audit/emails/engagement_approved.html'
        subject = f'Engagement Approved: {engagement.title}'
    elif status == 'rejected':
        template = 'audit/emails/engagement_rejected.html'
        subject = f'Engagement Rejected: {engagement.title}'
    else:
        # Invalid status
        return False
    
    # Get base URL for links in emails
    base_url = settings.BASE_URL if hasattr(settings, 'BASE_URL') else ''
    
    # If we have a request object, use it to build absolute URLs
    if request:
        base_url = request.build_absolute_uri('/').rstrip('/')
    
    # Build the engagement detail URL
    engagement_url = f"{base_url}{reverse('audit:engagement-detail', kwargs={'pk': engagement.pk})}"
    
    context = {
        'engagement': engagement,
        'engagement_url': engagement_url,
        'organization': engagement.organization,
        'requester': request.user,
    }
    
    if status == 'submitted':
        # Notify approvers using the new approval hierarchy
        approvers = get_engagement_approvers(engagement.organization)
        
        if not approvers.exists():
            # Fallback: notify admins if no managers exist
            approvers = User.objects.filter(
                organization=engagement.organization,
                role='admin'
            )
        
        for approver in approvers:
            context['approver'] = approver
            _send_templated_email(
                subject=subject,
                template=template,
                context=context,
                recipient_email=approver.email
            )
            
    elif status == 'approved' or status == 'rejected':
        # Notify the submitter
        # Get the owner/creator of the engagement
        if hasattr(engagement, 'created_by') and engagement.created_by:
            context['requester'] = engagement.created_by
            
            # Get the last approval record for this engagement
            from .models import Approval
            from django.contrib.contenttypes.models import ContentType
            
            approval = Approval.objects.filter(
                content_type=ContentType.objects.get_for_model(engagement),
                object_id=engagement.pk,
                status=status
            ).order_by('-updated_at').first()
            
            if approval:
                context['approval'] = approval
                context['approver'] = approval.approver
            
            _send_templated_email(
                subject=subject,
                template=template,
                context=context,
                recipient_email=engagement.created_by.email
            )
        # Notify approvers
        subject = _("Engagement submitted for approval: {0}").format(engagement.title)
        template = 'audit/emails/engagement_submitted.html'
        
        # Find users with approval permission
        approvers = User.objects.filter(
            groups__permissions__codename='can_approve_engagement', 
            groups__permissions__content_type__app_label='audit',
            organization=engagement.organization
        ).distinct()
        
        for approver in approvers:
            context['recipient'] = approver
            _send_templated_email(
                subject=subject,
                template=template,
                context=context,
                recipient_email=approver.email
            )
            
    elif status == 'approved' or status == 'rejected':
        # Notify the submitter and the assigned team
        action = 'approved' if status == 'approved' else 'rejected'
        subject = _("Engagement {0}: {1}").format(action, engagement.title)
        template = f'audit/emails/engagement_{action}.html'
        
        # Collect recipients (creator, assigned_to, assigned_by)
        recipients = []
        
        if hasattr(engagement, 'created_by') and engagement.created_by:
            recipients.append(engagement.created_by)
            
        if hasattr(engagement, 'assigned_to') and engagement.assigned_to:
            recipients.append(engagement.assigned_to)
            
        if hasattr(engagement, 'assigned_by') and engagement.assigned_by:
            recipients.append(engagement.assigned_by)
        
        # Remove duplicates
        recipients = list(set(recipients))
        
        for recipient in recipients:
            context['recipient'] = recipient
            _send_templated_email(
                subject=subject,
                template=template,
                context=context,
                recipient_email=recipient.email
            )


def send_risk_status_notification(risk, old_status, new_status, request=None):
    """Send email when risk status changes."""
    site_name = getattr(settings, 'SITE_NAME', "Audit Management System")
    recipients = []

    if risk.created_by and risk.created_by.email:
        recipients.append(risk.created_by.email)

    if risk.objective and risk.objective.engagement:
        engagement = risk.objective.engagement
        if engagement.lead and engagement.lead.email and engagement.lead.email not in recipients:
            recipients.append(engagement.lead.email)

    if not recipients:
        return

    subject = _(f'Risk Status Changed: {risk.title}')
    template = 'audit/emails/risk_status_changed.html'

    context = {
        'risk': risk,
        'old_status': old_status,
        'new_status': new_status,
        'site_name': site_name,
        'site_domain': settings.SITE_DOMAIN,
    }

    for email in recipients:
        _send_templated_email(subject, template, context, email)
        logger.info(f"Risk status email sent to {email} for risk {risk.id}")


def send_risk_approval_notification(risk, status, request=None):
    """Send email when risk approval status changes."""
    site_name = getattr(settings, 'SITE_NAME', "Audit Management System")
    recipients = []
    template = ''
    subject = ''

    if status == 'submitted':
        if risk.objective and risk.objective.engagement and risk.objective.engagement.lead:
            recipients.append(risk.objective.engagement.lead.email)
        if not recipients and risk.organization.approval_group:
            recipients = list(risk.organization.approval_group.user_set.values_list('email', flat=True))
        subject = _(f'Risk Assessment Submitted for Approval: {risk.title}')
        template = 'audit/emails/risk_submitted.html'
    elif status == 'approved':
        if risk.created_by and risk.created_by.email:
            recipients = [risk.created_by.email]
        subject = _(f'Risk Assessment Approved: {risk.title}')
        template = 'audit/emails/risk_approved.html'
    elif status == 'rejected':
        if risk.created_by and risk.created_by.email:
            recipients = [risk.created_by.email]
        subject = _(f'Risk Assessment Needs Revision: {risk.title}')
        template = 'audit/emails/risk_rejected.html'

    if not recipients:
        return

    context = {
        'risk': risk,
        'status': status,
        'site_name': site_name,
        'site_domain': settings.SITE_DOMAIN,
    }

    for email in recipients:
        _send_templated_email(subject, template, context, email)
        logger.info(f"Risk approval email ({status}) sent to {email} for risk {risk.id}")


def send_risk_assignment_notification(risk, request=None):
    """Send email when a risk is assigned to someone."""
    if not risk.assigned_to or not risk.assigned_to.email:
        return

    site_name = getattr(settings, 'SITE_NAME', "Audit Management System")
    subject = _(f'Risk Assigned: {risk.title}')
    template = 'audit/emails/risk_assigned.html'

    context = {
        'risk': risk,
        'site_name': site_name,
        'site_domain': settings.SITE_DOMAIN,
    }

    _send_templated_email(subject, template, context, risk.assigned_to.email)
    logger.info(f"Risk assignment email sent to {risk.assigned_to.email} for risk {risk.id}")
