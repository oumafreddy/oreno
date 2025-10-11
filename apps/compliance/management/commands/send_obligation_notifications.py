# oreno\apps\compliance\management\commands\send_obligation_notifications.py

from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
import logging

from compliance.tasks import check_and_send_obligation_notifications

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Check and send compliance obligation notifications (due reminders and overdue alerts)'

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
            self.style.SUCCESS('Starting compliance obligation notification check...')
        )
        
        try:
            if options['dry_run']:
                self.stdout.write(
                    self.style.WARNING('DRY RUN MODE - No emails will be sent')
                )
                # In dry run mode, we would just show what would be sent
                # For now, we'll just run the task and show the results
                result = check_and_send_obligation_notifications()
                
                if result:
                    self.stdout.write(
                        self.style.SUCCESS(
                            f"Would send {result['due_reminders']} due reminders and "
                            f"{result['overdue_alerts']} overdue alerts"
                        )
                    )
                else:
                    self.stdout.write(
                        self.style.ERROR('Failed to check obligations')
                    )
            else:
                # Run the actual task
                result = check_and_send_obligation_notifications.delay()
                
                self.stdout.write(
                    self.style.SUCCESS(
                        f"Obligation notification task queued with ID: {result.id}"
                    )
                )
                
                # Wait for result (optional - remove if you want fire-and-forget)
                try:
                    task_result = result.get(timeout=30)
                    if task_result:
                        self.stdout.write(
                            self.style.SUCCESS(
                                f"Task completed: {task_result['due_reminders']} due reminders, "
                                f"{task_result['overdue_alerts']} overdue alerts sent"
                            )
                        )
                    else:
                        self.stdout.write(
                            self.style.ERROR('Task completed but returned no results')
                        )
                except Exception as e:
                    self.stdout.write(
                        self.style.WARNING(f"Task queued but result not available: {e}")
                    )
        
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error running obligation notifications: {e}')
            )
            logger.error(f'Error in send_obligation_notifications command: {e}')
            raise

        self.stdout.write(
            self.style.SUCCESS('Compliance obligation notification check completed.')
        )
