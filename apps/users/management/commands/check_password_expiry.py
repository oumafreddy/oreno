from django.core.management.base import BaseCommand
from django.utils import timezone
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings
from users.models import PasswordHistory, CustomUser
from datetime import timedelta
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Check for expired passwords and notify users'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be done without actually doing it',
        )
        parser.add_argument(
            '--notify-only',
            action='store_true',
            help='Only send notifications, do not expire passwords',
        )
        parser.add_argument(
            '--days-before',
            type=int,
            default=7,
            help='Number of days before expiry to send warning (default: 7)',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        notify_only = options['notify_only']
        days_before = options['days_before']
        
        self.stdout.write(self.style.SUCCESS('Starting password expiry check...'))
        
        # Get current time
        now = timezone.now()
        
        # Find expired passwords
        expired_passwords = PasswordHistory.objects.filter(
            expires_at__lt=now,
            expires_at__isnull=False
        ).select_related('user')
        
        # Find passwords expiring soon
        warning_date = now + timedelta(days=days_before)
        expiring_soon = PasswordHistory.objects.filter(
            expires_at__lte=warning_date,
            expires_at__gt=now,
            expires_at__isnull=False
        ).select_related('user')
        
        self.stdout.write(f'Found {expired_passwords.count()} expired passwords')
        self.stdout.write(f'Found {expiring_soon.count()} passwords expiring within {days_before} days')
        
        # Process expired passwords
        expired_count = 0
        for password_record in expired_passwords:
            user = password_record.user
            if not user.is_active:
                continue
                
            if dry_run:
                self.stdout.write(f'[DRY RUN] Would expire password for {user.email}')
            else:
                if not notify_only:
                    # Mark user as requiring password change
                    user.is_active = False
                    user.save(update_fields=['is_active'])
                    self.stdout.write(f'Deactivated user {user.email} due to expired password')
                
                # Send expiry notification
                self.send_expiry_notification(user, password_record, expired=True)
                expired_count += 1
        
        # Process passwords expiring soon
        warning_count = 0
        for password_record in expiring_soon:
            user = password_record.user
            if not user.is_active:
                continue
                
            days_until_expiry = (password_record.expires_at - now).days
            
            if dry_run:
                self.stdout.write(f'[DRY RUN] Would send warning to {user.email} ({days_until_expiry} days until expiry)')
            else:
                # Send warning notification
                self.send_expiry_notification(user, password_record, expired=False, days_until_expiry=days_until_expiry)
                warning_count += 1
        
        if dry_run:
            self.stdout.write(self.style.WARNING('DRY RUN - No actual changes made'))
        else:
            self.stdout.write(self.style.SUCCESS(f'Processed {expired_count} expired passwords'))
            self.stdout.write(self.style.SUCCESS(f'Sent {warning_count} warning notifications'))
    
    def send_expiry_notification(self, user, password_record, expired=False, days_until_expiry=None):
        """Send password expiry notification email"""
        try:
            if expired:
                subject = 'Your password has expired'
                template = 'users/email/password_expired.html'
                context = {
                    'user': user,
                    'expired_at': password_record.expires_at,
                }
            else:
                subject = f'Your password will expire in {days_until_expiry} days'
                template = 'users/email/password_expiring_soon.html'
                context = {
                    'user': user,
                    'expires_at': password_record.expires_at,
                    'days_until_expiry': days_until_expiry,
                }
            
            # Render email content
            html_message = render_to_string(template, context)
            text_message = render_to_string(template.replace('.html', '.txt'), context)
            
            # Send email
            send_mail(
                subject=subject,
                message=text_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],
                html_message=html_message,
                fail_silently=False,
            )
            
            self.stdout.write(f'Sent {subject.lower()} email to {user.email}')
            
        except Exception as e:
            logger.error(f'Failed to send password expiry notification to {user.email}: {e}')
            self.stdout.write(self.style.ERROR(f'Failed to send notification to {user.email}: {e}'))
