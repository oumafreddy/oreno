from django.core.management.base import BaseCommand
from django.utils import timezone
from core.utils import send_tenant_email as send_mail
from django.template.loader import render_to_string
from django.conf import settings
from users.models import PasswordHistory, CustomUser
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Check for compromised passwords and notify users'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be done without actually doing it',
        )
        parser.add_argument(
            '--notify-only',
            action='store_true',
            help='Only send notifications, do not force password changes',
        )
        parser.add_argument(
            '--user',
            type=str,
            help='Check specific user by email',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        notify_only = options['notify_only']
        user_email = options['user']
        
        self.stdout.write(self.style.SUCCESS('Starting compromised password check...'))
        
        # Get compromised passwords
        compromised_passwords = PasswordHistory.objects.filter(
            is_compromised=True
        ).select_related('user')
        
        if user_email:
            compromised_passwords = compromised_passwords.filter(user__email=user_email)
        
        self.stdout.write(f'Found {compromised_passwords.count()} compromised passwords')
        
        # Process compromised passwords
        processed_count = 0
        for password_record in compromised_passwords:
            user = password_record.user
            if not user.is_active:
                continue
                
            if dry_run:
                self.stdout.write(f'[DRY RUN] Would process compromised password for {user.email} (found in {password_record.breach_count} breaches)')
            else:
                if not notify_only:
                    # Mark user as requiring password change
                    user.is_active = False
                    user.save(update_fields=['is_active'])
                    self.stdout.write(f'Deactivated user {user.email} due to compromised password')
                
                # Send compromise notification
                self.send_compromise_notification(user, password_record)
                processed_count += 1
        
        if dry_run:
            self.stdout.write(self.style.WARNING('DRY RUN - No actual changes made'))
        else:
            self.stdout.write(self.style.SUCCESS(f'Processed {processed_count} compromised passwords'))
    
    def send_compromise_notification(self, user, password_record):
        """Send password compromise notification email"""
        try:
            subject = 'Your password has been compromised'
            template = 'users/email/password_compromised.html'
            context = {
                'user': user,
                'breach_count': password_record.breach_count,
                'compromised_at': password_record.last_checked,
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
            
            self.stdout.write(f'Sent compromise notification email to {user.email}')
            
        except Exception as e:
            logger.error(f'Failed to send password compromise notification to {user.email}: {e}')
            self.stdout.write(self.style.ERROR(f'Failed to send notification to {user.email}: {e}'))
