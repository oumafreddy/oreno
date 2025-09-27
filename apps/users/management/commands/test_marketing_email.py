"""
Management command to test the marketing email functionality.
Usage: python manage.py test_marketing_email --email test@example.com
"""
from django.core.management.base import BaseCommand, CommandError
from django.template.loader import render_to_string
from django.core.mail import send_mail
from django.conf import settings
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Test the marketing email functionality for non-existent accounts'

    def add_arguments(self, parser):
        parser.add_argument(
            '--email',
            type=str,
            required=True,
            help='Email address to send marketing email to'
        )
        parser.add_argument(
            '--preview',
            action='store_true',
            help='Preview the email content without sending'
        )

    def handle(self, *args, **options):
        recipient_email = options['email']
        preview_mode = options['preview']

        self.stdout.write(self.style.SUCCESS(f"Testing marketing email for: {recipient_email}"))

        try:
            # Render the marketing email templates
            html_message = render_to_string('users/email/marketing_flyer.html')
            text_message = render_to_string('users/email/marketing_flyer.txt')

            if preview_mode:
                self.stdout.write(self.style.WARNING("PREVIEW MODE - Email content:"))
                self.stdout.write("=" * 50)
                self.stdout.write("HTML VERSION (first 500 chars):")
                self.stdout.write(html_message[:500] + "...")
                self.stdout.write("\n" + "=" * 50)
                self.stdout.write("TEXT VERSION (first 500 chars):")
                self.stdout.write(text_message[:500] + "...")
                self.stdout.write("=" * 50)
            else:
                # Send the marketing email
                send_mail(
                    subject='Welcome to Oreno GRC - Enterprise Governance, Risk & Compliance Platform',
                    message=text_message,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[recipient_email],
                    html_message=html_message,
                    fail_silently=False,
                )
                
                self.stdout.write(self.style.SUCCESS("Marketing email sent successfully!"))
                logger.info(f"Test marketing email sent to: {recipient_email}")

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Failed to send marketing email: {e}"))
            logger.error(f"Failed to send test marketing email to {recipient_email}: {e}")
            raise CommandError(f"Marketing email test failed: {e}")

        self.stdout.write(self.style.SUCCESS("Marketing email test completed."))
