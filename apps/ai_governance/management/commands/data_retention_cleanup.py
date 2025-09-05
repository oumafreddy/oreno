# oreno/apps/ai_governance/management/commands/data_retention_cleanup.py

from django.core.management.base import BaseCommand, CommandError
from django_tenants.utils import tenant_context
from django.utils import timezone
import logging

from organizations.models import Organization
from ai_governance.security import data_retention_service
from ai_governance.models import (
    TestRun, TestResult, Metric, EvidenceArtifact
)

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Clean up expired AI governance data according to retention policies'

    def add_arguments(self, parser):
        parser.add_argument(
            '--organization',
            type=int,
            help='Organization ID to clean up (required)',
            required=True
        )
        parser.add_argument(
            '--data-type',
            choices=['test_runs', 'test_results', 'metrics', 'artifacts', 'all'],
            default='all',
            help='Type of data to clean up'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be deleted without actually deleting'
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force cleanup without confirmation prompt'
        )
        parser.add_argument(
            '--retention-days',
            type=int,
            help='Override default retention period (in days)'
        )

    def handle(self, *args, **options):
        organization_id = options['organization']
        data_type = options['data_type']
        dry_run = options['dry_run']
        force = options['force']
        retention_days = options.get('retention_days')

        try:
            # Get organization
            try:
                org = Organization.objects.get(id=organization_id)
            except Organization.DoesNotExist:
                raise CommandError(f'Organization with ID {organization_id} not found')

            self.stdout.write(
                self.style.SUCCESS(f'Starting data retention cleanup for organization: {org.name}')
            )

            if dry_run:
                self.stdout.write(self.style.WARNING('DRY RUN MODE - No data will be deleted'))

            # Run cleanup within tenant context
            with tenant_context(org):
                cleanup_results = []

                # Define data types to process
                if data_type == 'all':
                    data_types = ['test_runs', 'test_results', 'metrics', 'artifacts']
                else:
                    data_types = [data_type]

                # Process each data type
                for dt in data_types:
                    self.stdout.write(f"Processing {dt}...")
                    
                    # Override retention period if specified
                    if retention_days:
                        data_retention_service.retention_periods[dt] = retention_days
                        self.stdout.write(f"Using custom retention period: {retention_days} days")

                    # Get model class for data type
                    model_class = self._get_model_class(dt)
                    if not model_class:
                        self.stdout.write(self.style.WARNING(f"Unknown data type: {dt}"))
                        continue

                    # Run cleanup
                    result = data_retention_service.cleanup_expired_data(
                        model_class, dt, dry_run=dry_run
                    )
                    cleanup_results.append(result)

                    # Display results
                    self._display_cleanup_result(dt, result)

                # Summary
                self._display_cleanup_summary(cleanup_results, dry_run)

                # Confirmation for actual deletion
                if not dry_run and not force:
                    if any(result['expired_count'] > 0 for result in cleanup_results):
                        confirm = input('\nProceed with deletion? (yes/no): ')
                        if confirm.lower() != 'yes':
                            self.stdout.write(self.style.WARNING('Cleanup cancelled'))
                            return

                        # Re-run cleanup without dry-run
                        self.stdout.write("Performing actual cleanup...")
                        final_results = []
                        for dt in data_types:
                            model_class = self._get_model_class(dt)
                            if model_class:
                                result = data_retention_service.cleanup_expired_data(
                                    model_class, dt, dry_run=False
                                )
                                final_results.append(result)
                                self._display_cleanup_result(dt, result)

                        self._display_cleanup_summary(final_results, dry_run=False)

        except Exception as e:
            logger.error(f"Data retention cleanup failed: {e}")
            raise CommandError(f'Data retention cleanup failed: {e}')

    def _get_model_class(self, data_type):
        """Get model class for data type."""
        model_mapping = {
            'test_runs': TestRun,
            'test_results': TestResult,
            'metrics': Metric,
            'artifacts': EvidenceArtifact,
        }
        return model_mapping.get(data_type)

    def _display_cleanup_result(self, data_type, result):
        """Display cleanup result for a data type."""
        expired_count = result['expired_count']
        deleted_count = result['deleted_count']
        
        if expired_count == 0:
            self.stdout.write(f"  {data_type}: No expired records found")
        else:
            if result.get('dry_run', False):
                self.stdout.write(
                    self.style.WARNING(f"  {data_type}: {expired_count} expired records would be deleted")
                )
            else:
                self.stdout.write(
                    self.style.SUCCESS(f"  {data_type}: {deleted_count} expired records deleted")
                )

    def _display_cleanup_summary(self, cleanup_results, dry_run):
        """Display cleanup summary."""
        self.stdout.write("")
        self.stdout.write("=" * 50)
        self.stdout.write("CLEANUP SUMMARY")
        self.stdout.write("=" * 50)
        
        total_expired = sum(result['expired_count'] for result in cleanup_results)
        total_deleted = sum(result['deleted_count'] for result in cleanup_results)
        
        if dry_run:
            self.stdout.write(f"Total expired records: {total_expired}")
            self.stdout.write(self.style.WARNING("DRY RUN - No records were actually deleted"))
        else:
            self.stdout.write(f"Total expired records: {total_expired}")
            self.stdout.write(f"Total deleted records: {total_deleted}")
            self.stdout.write(self.style.SUCCESS("Cleanup completed successfully"))

        # Show retention periods used
        self.stdout.write("")
        self.stdout.write("Retention periods used:")
        for data_type, days in data_retention_service.retention_periods.items():
            self.stdout.write(f"  {data_type}: {days} days")

        self.stdout.write("")
