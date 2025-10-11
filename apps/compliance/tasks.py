# oreno\apps\compliance\tasks.py

from celery import shared_task
from django.utils import timezone
from django.template.loader import render_to_string
from django.urls import reverse
from django.conf import settings
from datetime import timedelta
import logging

from .models import ComplianceObligation
from core.utils import send_tenant_email

logger = logging.getLogger(__name__)


@shared_task
def send_obligation_due_reminder(obligation_id, organization_id):
    """
    Send email reminder for compliance obligation due in 7 days
    """
    try:
        from organizations.models import Organization
        
        obligation = ComplianceObligation.objects.select_related(
            'requirement', 'owner', 'organization'
        ).get(id=obligation_id, organization_id=organization_id)
        
        organization = obligation.organization
        
        # Determine recipient email
        if obligation.owner:
            recipient_email = obligation.owner.email
            owner_name = obligation.owner.get_full_name() or obligation.owner.email
        elif obligation.owner_email:
            recipient_email = obligation.owner_email
            owner_name = obligation.owner_email
        else:
            logger.warning(f"No owner email found for obligation {obligation.obligation_id}")
            return False
        
        # Build obligation URL
        obligation_url = f"{settings.BASE_URL}{reverse('compliance:obligation_detail', kwargs={'pk': obligation.id})}"
        
        # Prepare email context
        context = {
            'obligation': obligation,
            'organization': organization,
            'owner_name': owner_name,
            'obligation_url': obligation_url,
        }
        
        # Render email template
        html_message = render_to_string('compliance/emails/obligation_due_reminder.html', context)
        
        # Send email
        subject = f"⚠️ Compliance Obligation Due Soon - {obligation.obligation_id}"
        
        success = send_tenant_email(
            subject=subject,
            message="",  # Plain text version not needed for HTML emails
            recipient_list=[recipient_email],
            request_or_org=organization,
            html_message=html_message,
            fail_silently=False
        )
        
        if success:
            logger.info(f"Obligation due reminder sent to {recipient_email} for obligation {obligation.obligation_id}")
        else:
            logger.error(f"Failed to send obligation due reminder to {recipient_email} for obligation {obligation.obligation_id}")
        
        return success
        
    except ComplianceObligation.DoesNotExist:
        logger.error(f"Obligation {obligation_id} not found")
        return False
    except Exception as e:
        logger.error(f"Error sending obligation due reminder: {e}")
        return False


@shared_task
def send_obligation_overdue_alert(obligation_id, organization_id):
    """
    Send email alert for overdue compliance obligation
    """
    try:
        from organizations.models import Organization
        
        obligation = ComplianceObligation.objects.select_related(
            'requirement', 'owner', 'organization'
        ).get(id=obligation_id, organization_id=organization_id)
        
        organization = obligation.organization
        
        # Determine recipient email
        if obligation.owner:
            recipient_email = obligation.owner.email
            owner_name = obligation.owner.get_full_name() or obligation.owner.email
        elif obligation.owner_email:
            recipient_email = obligation.owner_email
            owner_name = obligation.owner_email
        else:
            logger.warning(f"No owner email found for obligation {obligation.obligation_id}")
            return False
        
        # Calculate days overdue
        days_overdue = (timezone.now().date() - obligation.due_date).days
        
        # Build obligation URL
        obligation_url = f"{settings.BASE_URL}{reverse('compliance:obligation_detail', kwargs={'pk': obligation.id})}"
        
        # Prepare email context
        context = {
            'obligation': obligation,
            'organization': organization,
            'owner_name': owner_name,
            'obligation_url': obligation_url,
            'days_overdue': days_overdue,
        }
        
        # Render email template
        html_message = render_to_string('compliance/emails/obligation_overdue_alert.html', context)
        
        # Send email
        subject = f"🚨 Compliance Obligation Overdue - {obligation.obligation_id}"
        
        success = send_tenant_email(
            subject=subject,
            message="",  # Plain text version not needed for HTML emails
            recipient_list=[recipient_email],
            request_or_org=organization,
            html_message=html_message,
            fail_silently=False
        )
        
        if success:
            logger.info(f"Obligation overdue alert sent to {recipient_email} for obligation {obligation.obligation_id}")
        else:
            logger.error(f"Failed to send obligation overdue alert to {recipient_email} for obligation {obligation.obligation_id}")
        
        return success
        
    except ComplianceObligation.DoesNotExist:
        logger.error(f"Obligation {obligation_id} not found")
        return False
    except Exception as e:
        logger.error(f"Error sending obligation overdue alert: {e}")
        return False


@shared_task
def check_and_send_obligation_notifications():
    """
    Check all active obligations and send notifications for due/overdue items
    This task should be run daily via cron
    """
    try:
        today = timezone.now().date()
        seven_days_from_now = today + timedelta(days=7)
        one_day_ago = today - timedelta(days=1)
        
        # Get obligations due in 7 days (for reminders)
        due_obligations = ComplianceObligation.objects.filter(
            is_active=True,
            status__in=['open', 'in_progress'],
            due_date=seven_days_from_now
        ).select_related('requirement', 'owner', 'organization')
        
        # Get obligations overdue by 1 day (for alerts)
        overdue_obligations = ComplianceObligation.objects.filter(
            is_active=True,
            status__in=['open', 'in_progress'],
            due_date=one_day_ago
        ).select_related('requirement', 'owner', 'organization')
        
        # Send due reminders
        due_count = 0
        for obligation in due_obligations:
            if obligation.owner or obligation.owner_email:
                send_obligation_due_reminder.delay(obligation.id, obligation.organization.id)
                due_count += 1
        
        # Send overdue alerts
        overdue_count = 0
        for obligation in overdue_obligations:
            if obligation.owner or obligation.owner_email:
                send_obligation_overdue_alert.delay(obligation.id, obligation.organization.id)
                overdue_count += 1
        
        logger.info(f"Obligation notifications: {due_count} due reminders, {overdue_count} overdue alerts queued")
        
        return {
            'due_reminders': due_count,
            'overdue_alerts': overdue_count,
            'total_processed': due_count + overdue_count
        }
        
    except Exception as e:
        logger.error(f"Error in check_and_send_obligation_notifications: {e}")
        return False
