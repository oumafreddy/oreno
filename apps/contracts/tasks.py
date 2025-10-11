# oreno\apps\contracts\tasks.py

from celery import shared_task
from django.utils import timezone
from django.template.loader import render_to_string
from django.urls import reverse
from django.conf import settings
from datetime import timedelta
import logging

from .models import ContractMilestone
from core.utils import send_tenant_email

logger = logging.getLogger(__name__)


@shared_task
def send_milestone_due_reminder(milestone_id, organization_id):
    """
    Send email reminder for contract milestone due in 7 days
    """
    try:
        from organizations.models import Organization
        
        milestone = ContractMilestone.objects.select_related(
            'contract', 'organization'
        ).get(id=milestone_id, organization_id=organization_id)
        
        organization = milestone.organization
        
        # For milestones, we need to get the contract owner or primary party
        # Since milestones don't have direct owners, we'll use contract parties
        recipient_email = None
        owner_name = None
        
        # Try to get primary party contact email
        primary_party = milestone.contract.parties.filter(
            contractparty__is_primary_party=True
        ).first()
        
        if primary_party and primary_party.contact_email:
            recipient_email = primary_party.contact_email
            owner_name = primary_party.contact_person or primary_party.name
        else:
            # Fallback to any party with contact email
            party_with_email = milestone.contract.parties.filter(
                contact_email__isnull=False
            ).exclude(contact_email='').first()
            
            if party_with_email:
                recipient_email = party_with_email.contact_email
                owner_name = party_with_email.contact_person or party_with_email.name
        
        if not recipient_email:
            logger.warning(f"No contact email found for milestone {milestone.title} in contract {milestone.contract.code}")
            return False
        
        # Build milestone URL
        milestone_url = f"{settings.BASE_URL}{reverse('contracts:milestone_detail', kwargs={'pk': milestone.id})}"
        
        # Prepare email context
        context = {
            'milestone': milestone,
            'organization': organization,
            'owner_name': owner_name,
            'milestone_url': milestone_url,
        }
        
        # Render email template
        html_message = render_to_string('contracts/emails/milestone_due_reminder.html', context)
        
        # Send email
        subject = f"📅 Contract Milestone Due Soon - {milestone.contract.code}"
        
        success = send_tenant_email(
            subject=subject,
            message="",  # Plain text version not needed for HTML emails
            recipient_list=[recipient_email],
            request_or_org=organization,
            html_message=html_message,
            fail_silently=False
        )
        
        if success:
            logger.info(f"Milestone due reminder sent to {recipient_email} for milestone {milestone.title}")
        else:
            logger.error(f"Failed to send milestone due reminder to {recipient_email} for milestone {milestone.title}")
        
        return success
        
    except ContractMilestone.DoesNotExist:
        logger.error(f"Milestone {milestone_id} not found")
        return False
    except Exception as e:
        logger.error(f"Error sending milestone due reminder: {e}")
        return False


@shared_task
def send_milestone_overdue_alert(milestone_id, organization_id):
    """
    Send email alert for overdue contract milestone
    """
    try:
        from organizations.models import Organization
        
        milestone = ContractMilestone.objects.select_related(
            'contract', 'organization'
        ).get(id=milestone_id, organization_id=organization_id)
        
        organization = milestone.organization
        
        # For milestones, we need to get the contract owner or primary party
        # Since milestones don't have direct owners, we'll use contract parties
        recipient_email = None
        owner_name = None
        
        # Try to get primary party contact email
        primary_party = milestone.contract.parties.filter(
            contractparty__is_primary_party=True
        ).first()
        
        if primary_party and primary_party.contact_email:
            recipient_email = primary_party.contact_email
            owner_name = primary_party.contact_person or primary_party.name
        else:
            # Fallback to any party with contact email
            party_with_email = milestone.contract.parties.filter(
                contact_email__isnull=False
            ).exclude(contact_email='').first()
            
            if party_with_email:
                recipient_email = party_with_email.contact_email
                owner_name = party_with_email.contact_person or party_with_email.name
        
        if not recipient_email:
            logger.warning(f"No contact email found for milestone {milestone.title} in contract {milestone.contract.code}")
            return False
        
        # Calculate days overdue
        days_overdue = (timezone.now().date() - milestone.due_date).days
        
        # Build milestone URL
        milestone_url = f"{settings.BASE_URL}{reverse('contracts:milestone_detail', kwargs={'pk': milestone.id})}"
        
        # Prepare email context
        context = {
            'milestone': milestone,
            'organization': organization,
            'owner_name': owner_name,
            'milestone_url': milestone_url,
            'days_overdue': days_overdue,
        }
        
        # Render email template
        html_message = render_to_string('contracts/emails/milestone_overdue_alert.html', context)
        
        # Send email
        subject = f"🚨 Contract Milestone Overdue - {milestone.contract.code}"
        
        success = send_tenant_email(
            subject=subject,
            message="",  # Plain text version not needed for HTML emails
            recipient_list=[recipient_email],
            request_or_org=organization,
            html_message=html_message,
            fail_silently=False
        )
        
        if success:
            logger.info(f"Milestone overdue alert sent to {recipient_email} for milestone {milestone.title}")
        else:
            logger.error(f"Failed to send milestone overdue alert to {recipient_email} for milestone {milestone.title}")
        
        return success
        
    except ContractMilestone.DoesNotExist:
        logger.error(f"Milestone {milestone_id} not found")
        return False
    except Exception as e:
        logger.error(f"Error sending milestone overdue alert: {e}")
        return False


@shared_task
def check_and_send_milestone_notifications():
    """
    Check all active milestones and send notifications for due/overdue items
    This task should be run daily via cron
    """
    try:
        today = timezone.now().date()
        seven_days_from_now = today + timedelta(days=7)
        one_day_ago = today - timedelta(days=1)
        
        # Get milestones due in 7 days (for reminders)
        due_milestones = ContractMilestone.objects.filter(
            is_completed=False,
            due_date=seven_days_from_now
        ).select_related('contract', 'organization')
        
        # Get milestones overdue by 1 day (for alerts)
        overdue_milestones = ContractMilestone.objects.filter(
            is_completed=False,
            due_date=one_day_ago
        ).select_related('contract', 'organization')
        
        # Send due reminders
        due_count = 0
        for milestone in due_milestones:
            # Check if milestone has contact email
            has_contact = milestone.contract.parties.filter(
                contact_email__isnull=False
            ).exclude(contact_email='').exists()
            
            if has_contact:
                send_milestone_due_reminder.delay(milestone.id, milestone.organization.id)
                due_count += 1
        
        # Send overdue alerts
        overdue_count = 0
        for milestone in overdue_milestones:
            # Check if milestone has contact email
            has_contact = milestone.contract.parties.filter(
                contact_email__isnull=False
            ).exclude(contact_email='').exists()
            
            if has_contact:
                send_milestone_overdue_alert.delay(milestone.id, milestone.organization.id)
                overdue_count += 1
        
        logger.info(f"Milestone notifications: {due_count} due reminders, {overdue_count} overdue alerts queued")
        
        return {
            'due_reminders': due_count,
            'overdue_alerts': overdue_count,
            'total_processed': due_count + overdue_count
        }
        
    except Exception as e:
        logger.error(f"Error in check_and_send_milestone_notifications: {e}")
        return False
