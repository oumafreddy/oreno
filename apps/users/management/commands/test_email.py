"""
Management command to test email functionality in production.
Usage: python manage.py test_email --email test@example.com
"""
from django.core.management.base import BaseCommand, CommandError
from django.core.mail import send_mail as django_send_mail
from django.conf import settings
from core.utils import send_tenant_email
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Test email functionality with both tenant and standard Django email backends'

    def add_arguments(self, parser):
        parser.add_argument(
            '--email',
            type=str,
            required=True,
            help='Email address to send test email to'
        )
        parser.add_argument(
            '--test-type',
            type=str,
            choices=['both', 'tenant', 'django'],
            default='both',
            help='Type of email test to run (default: both)'
        )

    def handle(self, *args, **options):
        email = options['email']
        test_type = options['test_type']
        
        self.stdout.write(f"Testing email functionality for: {email}")
        self.stdout.write(f"Email backend: {settings.EMAIL_BACKEND}")
        self.stdout.write(f"Email host: {settings.EMAIL_HOST}")
        self.stdout.write(f"Email port: {settings.EMAIL_PORT}")
        self.stdout.write(f"Email use TLS: {settings.EMAIL_USE_TLS}")
        self.stdout.write(f"Email use SSL: {settings.EMAIL_USE_SSL}")
        self.stdout.write("-" * 50)
        
        success_count = 0
        total_tests = 0
        
        if test_type in ['both', 'django']:
            total_tests += 1
            self.stdout.write("Testing Django standard send_mail...")
            try:
                django_send_mail(
                    subject="Test Email - Django Standard",
                    message="This is a test email sent using Django's standard send_mail function.",
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[email],
                    fail_silently=False,
                )
                self.stdout.write(self.style.SUCCESS("✓ Django standard send_mail: SUCCESS"))
                success_count += 1
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"✗ Django standard send_mail: FAILED - {e}"))
                logger.error(f"Django standard send_mail failed: {e}")
        
        if test_type in ['both', 'tenant']:
            total_tests += 1
            self.stdout.write("Testing tenant email function...")
            try:
                send_tenant_email(
                    subject="Test Email - Tenant Function",
                    message="This is a test email sent using the tenant email function.",
                    recipient_list=[email],
                    fail_silently=False,
                )
                self.stdout.write(self.style.SUCCESS("✓ Tenant email function: SUCCESS"))
                success_count += 1
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"✗ Tenant email function: FAILED - {e}"))
                logger.error(f"Tenant email function failed: {e}")
        
        self.stdout.write("-" * 50)
        self.stdout.write(f"Test Results: {success_count}/{total_tests} tests passed")
        
        if success_count == total_tests:
            self.stdout.write(self.style.SUCCESS("All email tests passed! ✓"))
        elif success_count > 0:
            self.stdout.write(self.style.WARNING("Some email tests passed. Check logs for details."))
        else:
            self.stdout.write(self.style.ERROR("All email tests failed! Check your email configuration."))
