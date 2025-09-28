# apps/users/management/commands/test_password_change_email.py
"""
Management command to test password change email notifications.
This command helps verify that email notifications are working correctly.
"""

from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth import get_user_model
from django.utils import timezone
from users.email_utils import send_password_change_notification
from users.models import UserEmailPreferences, EmailLog
import logging

logger = logging.getLogger(__name__)

User = get_user_model()


class Command(BaseCommand):
    help = 'Test password change email notifications'

    def add_arguments(self, parser):
        parser.add_argument(
            '--email',
            type=str,
            help='Email address to send test notification to',
        )
        parser.add_argument(
            '--user-id',
            type=int,
            help='User ID to send test notification to',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be sent without actually sending emails',
        )
        parser.add_argument(
            '--check-preferences',
            action='store_true',
            help='Check user email preferences before sending',
        )
        parser.add_argument(
            '--show-logs',
            action='store_true',
            help='Show recent email logs after sending',
        )

    def handle(self, *args, **options):
        email = options.get('email')
        user_id = options.get('user_id')
        dry_run = options.get('dry_run', False)
        check_preferences = options.get('check_preferences', False)
        show_logs = options.get('show_logs', False)

        # Determine which user to test with
        user = None
        
        if user_id:
            try:
                user = User.objects.get(id=user_id)
            except User.DoesNotExist:
                raise CommandError(f'User with ID {user_id} does not exist')
        elif email:
            try:
                user = User.objects.get(email=email)
            except User.DoesNotExist:
                raise CommandError(f'User with email {email} does not exist')
        else:
            # Use the first available user
            user = User.objects.first()
            if not user:
                raise CommandError('No users found in the database')

        self.stdout.write(
            self.style.SUCCESS(f'Testing password change email for user: {user.email}')
        )

        # Check user email preferences if requested
        if check_preferences:
            try:
                preferences = UserEmailPreferences.get_or_create_preferences(user)
                self.stdout.write(f'Email preferences for {user.email}:')
                self.stdout.write(f'  Password change notifications: {preferences.password_change_notifications}')
                self.stdout.write(f'  Security alerts: {preferences.security_alerts}')
                self.stdout.write(f'  Notification frequency: {preferences.notification_frequency}')
                
                if not preferences.password_change_notifications:
                    self.stdout.write(
                        self.style.WARNING('WARNING: User has disabled password change notifications')
                    )
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'Error checking preferences: {e}')
                )

        # Show what would be sent in dry run
        if dry_run:
            self.stdout.write(
                self.style.WARNING('DRY RUN - No emails will be sent')
            )
            self.stdout.write(f'Would send password change notification to: {user.email}')
            self.stdout.write(f'User: {user.get_full_name() or user.username}')
            self.stdout.write(f'Organization: {user.organization.name if user.organization else "None"}')
            self.stdout.write(f'Password expiration period: {user.get_password_expiration_period_display()}')
            self.stdout.write(f'Expiration days: {user.get_password_expiration_days()}')
            return

        # Send the test email
        try:
            self.stdout.write('Sending password change notification...')
            
            # Simulate request context
            class MockRequest:
                def __init__(self, user):
                    self.user = user
                    self.organization = user.organization
                    self.META = {
                        'REMOTE_ADDR': '127.0.0.1',
                        'HTTP_USER_AGENT': 'Test Command/1.0'
                    }
            
            mock_request = MockRequest(user)
            
            success = send_password_change_notification(
                user=user,
                request=mock_request,
                ip_address='127.0.0.1',
                user_agent='Test Command/1.0'
            )
            
            if success:
                self.stdout.write(
                    self.style.SUCCESS('Password change notification sent successfully!')
                )
            else:
                self.stdout.write(
                    self.style.ERROR('Failed to send password change notification')
                )
                
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error sending notification: {e}')
            )
            logger.exception('Error in test_password_change_email command')

        # Show recent email logs if requested
        if show_logs:
            self.stdout.write('\nRecent email logs:')
            recent_logs = EmailLog.objects.filter(
                user=user,
                email_type='password_change'
            ).order_by('-created_at')[:5]
            
            if recent_logs:
                for log in recent_logs:
                    status_color = {
                        'sent': self.style.SUCCESS,
                        'failed': self.style.ERROR,
                        'skipped': self.style.WARNING,
                        'pending': self.style.WARNING,
                    }.get(log.status, self.style.NOTICE)
                    
                    self.stdout.write(
                        f'  {log.created_at.strftime("%Y-%m-%d %H:%M:%S")} - '
                        f'{status_color(log.status.upper())} - '
                        f'{log.subject}'
                    )
                    if log.error_message:
                        self.stdout.write(f'    Error: {log.error_message}')
            else:
                self.stdout.write('  No recent email logs found')

        # Show email statistics
        self.stdout.write('\nEmail statistics:')
        total_logs = EmailLog.objects.filter(user=user).count()
        sent_logs = EmailLog.objects.filter(user=user, status='sent').count()
        failed_logs = EmailLog.objects.filter(user=user, status='failed').count()
        skipped_logs = EmailLog.objects.filter(user=user, status='skipped').count()
        
        self.stdout.write(f'  Total emails: {total_logs}')
        self.stdout.write(f'  Sent: {sent_logs}')
        self.stdout.write(f'  Failed: {failed_logs}')
        self.stdout.write(f'  Skipped: {skipped_logs}')
        
        if total_logs > 0:
            success_rate = (sent_logs / total_logs) * 100
            self.stdout.write(f'  Success rate: {success_rate:.1f}%')
