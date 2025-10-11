# oreno\apps\core\management\commands\send_all_notifications.py

from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
import logging

from organizations.models import Organization
from compliance.models import ComplianceObligation
from contracts.models import ContractMilestone
from compliance.tasks import send_obligation_due_reminder, send_obligation_overdue_alert
from contracts.tasks import send_milestone_due_reminder, send_milestone_overdue_alert

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Check and send all notifications (compliance obligations and contract milestones)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be sent without actually sending emails',
        )
        parser.add_argument(
            '--organization',
            type=str,
            help='Limit to specific organization (by code)',
        )

    def handle(self, *args, **options):
        self.stdout.write(
            self.style.SUCCESS('Starting comprehensive notification check...')
        )
        
        today = timezone.now().date()
        due_in_7_days = today + timedelta(days=7)
        overdue_1_day = today - timedelta(days=1)
        
        total_due_reminders = 0
        total_overdue_alerts = 0
        
        # Get organizations to check
        if options['organization']:
            try:
                organizations = [Organization.objects.get(code=options['organization'])]
            except Organization.DoesNotExist:
                self.stdout.write(
                    self.style.ERROR(f'Organization with code "{options["organization"]}" not found')
                )
                return
        else:
            organizations = Organization.objects.all()
        
        try:
            # Check compliance obligations
            self.stdout.write(
                self.style.SUCCESS('Checking compliance obligations...')
            )
            
            obligation_due_reminders = 0
            obligation_overdue_alerts = 0
            
            for organization in organizations:
                self.stdout.write(f"  Checking organization: {organization.name}")
                
                # Due reminders (7 days before)
                upcoming_obligations = ComplianceObligation.objects.filter(
                    organization=organization,
                    due_date=due_in_7_days,
                    status__in=['open', 'in_progress']
                )
                
                for obligation in upcoming_obligations:
                    if options['dry_run']:
                        self.stdout.write(f"    [DRY RUN] Would send 7-day reminder for: {obligation.obligation_id}")
                    else:
                        send_obligation_due_reminder.delay(obligation.id, organization.id)
                        self.stdout.write(f"    Sent 7-day reminder for: {obligation.obligation_id}")
                    obligation_due_reminders += 1
                
                # Overdue alerts (1 day after due date)
                overdue_obligations = ComplianceObligation.objects.filter(
                    organization=organization,
                    due_date=overdue_1_day,
                    status__in=['open', 'in_progress']
                )
                
                for obligation in overdue_obligations:
                    if options['dry_run']:
                        self.stdout.write(f"    [DRY RUN] Would send overdue alert for: {obligation.obligation_id}")
                    else:
                        send_obligation_overdue_alert.delay(obligation.id, organization.id)
                        self.stdout.write(f"    Sent overdue alert for: {obligation.obligation_id}")
                    obligation_overdue_alerts += 1
            
            total_due_reminders += obligation_due_reminders
            total_overdue_alerts += obligation_overdue_alerts
            
            self.stdout.write(
                self.style.SUCCESS(
                    f"Compliance: {obligation_due_reminders} due reminders, "
                    f"{obligation_overdue_alerts} overdue alerts"
                )
            )
            
            # Check contract milestones
            self.stdout.write(
                self.style.SUCCESS('Checking contract milestones...')
            )
            
            milestone_due_reminders = 0
            milestone_overdue_alerts = 0
            
            for organization in organizations:
                self.stdout.write(f"  Checking organization: {organization.name}")
                
                # Due reminders (7 days before)
                upcoming_milestones = ContractMilestone.objects.filter(
                    organization=organization,
                    due_date=due_in_7_days,
                    is_completed=False
                )
                
                for milestone in upcoming_milestones:
                    if options['dry_run']:
                        self.stdout.write(f"    [DRY RUN] Would send 7-day reminder for: {milestone.title}")
                    else:
                        send_milestone_due_reminder.delay(milestone.id, organization.id)
                        self.stdout.write(f"    Sent 7-day reminder for: {milestone.title}")
                    milestone_due_reminders += 1
                
                # Overdue alerts (1 day after due date)
                overdue_milestones = ContractMilestone.objects.filter(
                    organization=organization,
                    due_date=overdue_1_day,
                    is_completed=False
                )
                
                for milestone in overdue_milestones:
                    if options['dry_run']:
                        self.stdout.write(f"    [DRY RUN] Would send overdue alert for: {milestone.title}")
                    else:
                        send_milestone_overdue_alert.delay(milestone.id, organization.id)
                        self.stdout.write(f"    Sent overdue alert for: {milestone.title}")
                    milestone_overdue_alerts += 1
            
            total_due_reminders += milestone_due_reminders
            total_overdue_alerts += milestone_overdue_alerts
            
            self.stdout.write(
                self.style.SUCCESS(
                    f"Contracts: {milestone_due_reminders} due reminders, "
                    f"{milestone_overdue_alerts} overdue alerts"
                )
            )
            
            # Summary
            self.stdout.write(
                self.style.SUCCESS(
                    f"\n=== SUMMARY ==="
                )
            )
            self.stdout.write(
                self.style.SUCCESS(
                    f"Total due reminders: {total_due_reminders}"
                )
            )
            self.stdout.write(
                self.style.SUCCESS(
                    f"Total overdue alerts: {total_overdue_alerts}"
                )
            )
            self.stdout.write(
                self.style.SUCCESS(
                    f"Total notifications: {total_due_reminders + total_overdue_alerts}"
                )
            )
        
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error running notifications: {e}')
            )
            logger.error(f'Error in send_all_notifications command: {e}')
            raise

        self.stdout.write(
            self.style.SUCCESS('Comprehensive notification check completed.')
        )
