"""
Management command to cleanup old test runs and artifacts.
Follows the same pattern as other management commands in the project.
"""

from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
from django.db import transaction
from django_tenants.utils import tenant_context
from organizations.models import Organization
from datetime import timedelta

from ai_governance.models import TestRun, EvidenceArtifact
from ai_governance.tasks import cleanup_old_test_runs


class Command(BaseCommand):
    help = 'Cleanup old AI governance test runs and artifacts'

    def add_arguments(self, parser):
        parser.add_argument(
            '--organization',
            type=int,
            help='Organization ID to cleanup for (optional, defaults to all)'
        )
        parser.add_argument(
            '--days-old',
            type=int,
            default=30,
            help='Delete test runs older than this many days (default: 30)'
        )
        parser.add_argument(
            '--status',
            type=str,
            choices=['completed', 'failed', 'cancelled'],
            help='Only cleanup test runs with specific status'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be deleted without actually deleting'
        )
        parser.add_argument(
            '--async',
            action='store_true',
            help='Run cleanup asynchronously using Celery'
        )
        parser.add_argument(
            '--include-artifacts',
            action='store_true',
            help='Also cleanup associated artifacts and files'
        )

    def handle(self, *args, **options):
        org_id = options.get('organization')
        days_old = options['days_old']
        status = options.get('status')
        dry_run = options['dry_run']
        run_async = options['async']
        include_artifacts = options['include_artifacts']

        cutoff_date = timezone.now() - timedelta(days=days_old)
        
        self.stdout.write(f'Cleaning up test runs older than {days_old} days (before {cutoff_date.date()})')
        
        if org_id:
            # Cleanup for specific organization
            try:
                org = Organization.objects.get(id=org_id)
                self._cleanup_organization(org, cutoff_date, status, dry_run, run_async, include_artifacts)
            except Organization.DoesNotExist:
                raise CommandError(f'Organization with ID {org_id} not found')
        else:
            # Cleanup for all organizations
            organizations = Organization.objects.all()
            self.stdout.write(f'Processing {organizations.count()} organizations...')
            
            for org in organizations:
                self.stdout.write(f'Processing organization: {org.name}')
                self._cleanup_organization(org, cutoff_date, status, dry_run, run_async, include_artifacts)

        self.stdout.write(self.style.SUCCESS('Cleanup command completed'))

    def _cleanup_organization(self, org, cutoff_date, status, dry_run, run_async, include_artifacts):
        """Cleanup test runs for a specific organization."""
        with tenant_context(org):
            # Build queryset for old test runs
            queryset = TestRun.objects.filter(
                organization=org,
                created_at__lt=cutoff_date
            )
            
            if status:
                queryset = queryset.filter(status=status)
            
            old_test_runs = queryset.all()
            count = old_test_runs.count()
            
            if count == 0:
                self.stdout.write(f'  No test runs to cleanup in {org.name}')
                return
            
            self.stdout.write(f'  Found {count} test runs to cleanup in {org.name}')
            
            if dry_run:
                self.stdout.write(self.style.WARNING('  DRY RUN - No test runs will be deleted'))
                for test_run in old_test_runs[:10]:  # Show first 10
                    self.stdout.write(f'    Would delete: {test_run.id} ({test_run.status}) - {test_run.created_at.date()}')
                if count > 10:
                    self.stdout.write(f'    ... and {count - 10} more')
                return
            
            if run_async:
                # Queue async cleanup
                test_run_ids = list(old_test_runs.values_list('id', flat=True))
                task = cleanup_old_test_runs.delay(days_old=30)  # Use default days for async
                self.stdout.write(f'  Queued async cleanup with task ID: {task.id}')
                return
            
            # Perform synchronous cleanup
            deleted_count = 0
            artifact_count = 0
            
            with transaction.atomic():
                for test_run in old_test_runs:
                    # Count artifacts if requested
                    if include_artifacts:
                        artifacts = EvidenceArtifact.objects.filter(test_run=test_run)
                        artifact_count += artifacts.count()
                        artifacts.delete()
                    
                    # Delete test run (this will cascade to related objects)
                    test_run.delete()
                    deleted_count += 1
                    
                    if deleted_count % 100 == 0:
                        self.stdout.write(f'  Deleted {deleted_count}/{count} test runs...')
            
            self.stdout.write(f'  Cleaned up {deleted_count} test runs in {org.name}')
            if include_artifacts:
                self.stdout.write(f'  Also deleted {artifact_count} associated artifacts')
