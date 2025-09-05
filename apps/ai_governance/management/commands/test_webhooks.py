"""
Management command to test webhook endpoints.
Follows the same pattern as other management commands in the project.
"""

from django.core.management.base import BaseCommand, CommandError
from django_tenants.utils import tenant_context
from organizations.models import Organization

from ai_governance.models import WebhookSubscription
from ai_governance.webhook_service import webhook_service


class Command(BaseCommand):
    help = 'Test AI governance webhook endpoints'

    def add_arguments(self, parser):
        parser.add_argument(
            '--organization',
            type=int,
            required=True,
            help='Organization ID to test webhooks for'
        )
        parser.add_argument(
            '--webhook-id',
            type=int,
            help='Test specific webhook by ID (optional)'
        )
        parser.add_argument(
            '--all',
            action='store_true',
            help='Test all active webhooks in the organization'
        )

    def handle(self, *args, **options):
        org_id = options['organization']
        webhook_id = options.get('webhook_id')
        test_all = options['all']

        try:
            # Get organization
            org = Organization.objects.get(id=org_id)
        except Organization.DoesNotExist:
            raise CommandError(f'Organization with ID {org_id} not found')

        with tenant_context(org):
            if webhook_id:
                # Test specific webhook
                try:
                    webhook = WebhookSubscription.objects.get(
                        organization=org,
                        id=webhook_id
                    )
                    self._test_webhook(webhook)
                except WebhookSubscription.DoesNotExist:
                    raise CommandError(f'Webhook with ID {webhook_id} not found in organization {org.name}')
            elif test_all:
                # Test all active webhooks
                webhooks = WebhookSubscription.objects.filter(
                    organization=org,
                    is_active=True
                )
                
                if not webhooks.exists():
                    self.stdout.write(self.style.WARNING(f'No active webhooks found in organization {org.name}'))
                    return
                
                self.stdout.write(f'Testing {webhooks.count()} active webhooks in {org.name}...')
                
                for webhook in webhooks:
                    self._test_webhook(webhook)
            else:
                raise CommandError('Please specify either --webhook-id or --all')

        self.stdout.write(self.style.SUCCESS('Webhook testing completed'))

    def _test_webhook(self, webhook: WebhookSubscription):
        """Test a specific webhook endpoint."""
        self.stdout.write(f'Testing webhook: {webhook.url}')
        
        try:
            result = webhook_service.test_webhook(webhook)
            
            if result['success']:
                self.stdout.write(self.style.SUCCESS(f'  ✓ Success: {result["message"]}'))
            else:
                self.stdout.write(self.style.ERROR(f'  ✗ Failed: {result["message"]}'))
                
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'  ✗ Error: {str(e)}'))
