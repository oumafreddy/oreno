"""
Management command to trigger AI governance test runs from CLI.
Follows the same pattern as other management commands in the project.
"""

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django_tenants.utils import tenant_context
from organizations.models import Organization

from ai_governance.models import ModelAsset, DatasetAsset, TestPlan, TestRun
from ai_governance.tasks import execute_test_run


class Command(BaseCommand):
    help = 'Trigger AI governance test runs from command line'

    def add_arguments(self, parser):
        parser.add_argument(
            '--organization',
            type=int,
            required=True,
            help='Organization ID to run tests for'
        )
        parser.add_argument(
            '--model',
            type=str,
            required=True,
            help='Model asset name to test'
        )
        parser.add_argument(
            '--dataset',
            type=str,
            help='Dataset asset name to test with (optional)'
        )
        parser.add_argument(
            '--test-plan',
            type=str,
            help='Test plan name to use (optional)'
        )
        parser.add_argument(
            '--test-categories',
            type=str,
            nargs='+',
            default=['fairness', 'explainability', 'robustness'],
            help='Test categories to run (default: fairness explainability robustness)'
        )
        parser.add_argument(
            '--async',
            action='store_true',
            help='Run tests asynchronously using Celery'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be done without actually running tests'
        )

    def handle(self, *args, **options):
        org_id = options['organization']
        model_name = options['model']
        dataset_name = options.get('dataset')
        test_plan_name = options.get('test_plan')
        test_categories = options['test_categories']
        run_async = options['async']
        dry_run = options['dry_run']

        try:
            # Get organization
            org = Organization.objects.get(id=org_id)
        except Organization.DoesNotExist:
            raise CommandError(f'Organization with ID {org_id} not found')

        with tenant_context(org):
            try:
                # Get model asset
                model_asset = ModelAsset.objects.get(
                    organization=org,
                    name=model_name
                )
                self.stdout.write(f'Found model: {model_asset.name} ({model_asset.model_type})')
            except ModelAsset.DoesNotExist:
                raise CommandError(f'Model asset "{model_name}" not found in organization {org.name}')

            # Get dataset asset if specified
            dataset_asset = None
            if dataset_name:
                try:
                    dataset_asset = DatasetAsset.objects.get(
                        organization=org,
                        name=dataset_name
                    )
                    self.stdout.write(f'Found dataset: {dataset_asset.name} ({dataset_asset.role})')
                except DatasetAsset.DoesNotExist:
                    raise CommandError(f'Dataset asset "{dataset_name}" not found in organization {org.name}')

            # Get test plan if specified
            test_plan = None
            if test_plan_name:
                try:
                    test_plan = TestPlan.objects.get(
                        organization=org,
                        name=test_plan_name
                    )
                    self.stdout.write(f'Found test plan: {test_plan.name}')
                except TestPlan.DoesNotExist:
                    raise CommandError(f'Test plan "{test_plan_name}" not found in organization {org.name}')

            if dry_run:
                self.stdout.write(self.style.WARNING('DRY RUN - No tests will be executed'))
                self.stdout.write(f'Would create test run with:')
                self.stdout.write(f'  Model: {model_asset.name}')
                if dataset_asset:
                    self.stdout.write(f'  Dataset: {dataset_asset.name}')
                if test_plan:
                    self.stdout.write(f'  Test Plan: {test_plan.name}')
                self.stdout.write(f'  Test Categories: {", ".join(test_categories)}')
                self.stdout.write(f'  Async: {run_async}')
                return

            # Create test run
            with transaction.atomic():
                test_run = TestRun.objects.create(
                    organization=org,
                    model_asset=model_asset,
                    dataset_asset=dataset_asset,
                    test_plan=test_plan,
                    parameters={
                        'test_categories': test_categories,
                        'triggered_by': 'cli',
                        'cli_command': 'trigger_test_run'
                    }
                )

                self.stdout.write(f'Created test run: {test_run.id}')

                if run_async:
                    # Queue async execution
                    task = execute_test_run.delay(test_run.id)
                    self.stdout.write(f'Queued async execution with task ID: {task.id}')
                    self.stdout.write('Use Celery monitoring to track progress')
                else:
                    # Run synchronously
                    self.stdout.write('Running tests synchronously...')
                    try:
                        result = execute_test_run(test_run.id)
                        if result:
                            self.stdout.write(self.style.SUCCESS('Test run completed successfully'))
                        else:
                            self.stdout.write(self.style.ERROR('Test run failed'))
                    except Exception as e:
                        self.stdout.write(self.style.ERROR(f'Test run failed with error: {e}'))

        self.stdout.write(self.style.SUCCESS('Command completed'))
