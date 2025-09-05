"""
Management command to sync models from external registries (MLflow, S3, etc.).
Follows the same pattern as other management commands in the project.
"""

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django_tenants.utils import tenant_context
from organizations.models import Organization

from ai_governance.models import ModelAsset, ConnectorConfig
from services.ai.governance_engine.connectors.mlflow import sync_models_from_mlflow


class Command(BaseCommand):
    help = 'Sync AI models from external registries to AI governance'

    def add_arguments(self, parser):
        parser.add_argument(
            '--organization',
            type=int,
            required=True,
            help='Organization ID to sync models for'
        )
        parser.add_argument(
            '--connector',
            type=str,
            help='Connector name to use for syncing (optional)'
        )
        parser.add_argument(
            '--connector-type',
            type=str,
            choices=['mlflow', 's3', 'azure_blob'],
            default='mlflow',
            help='Type of connector to use (default: mlflow)'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be synced without actually creating records'
        )
        parser.add_argument(
            '--update-existing',
            action='store_true',
            help='Update existing model assets if found'
        )

    def handle(self, *args, **options):
        org_id = options['organization']
        connector_name = options.get('connector')
        connector_type = options['connector_type']
        dry_run = options['dry_run']
        update_existing = options['update_existing']

        try:
            # Get organization
            org = Organization.objects.get(id=org_id)
        except Organization.DoesNotExist:
            raise CommandError(f'Organization with ID {org_id} not found')

        with tenant_context(org):
            # Get or create connector config
            if connector_name:
                try:
                    connector = ConnectorConfig.objects.get(
                        organization=org,
                        name=connector_name,
                        connector_type=connector_type
                    )
                    self.stdout.write(f'Using existing connector: {connector.name}')
                except ConnectorConfig.DoesNotExist:
                    raise CommandError(f'Connector "{connector_name}" not found')
            else:
                # Use default connector or create one
                connector, created = ConnectorConfig.objects.get_or_create(
                    organization=org,
                    name=f'default_{connector_type}',
                    connector_type=connector_type,
                    defaults={
                        'config': {
                            'tracking_uri': 'http://localhost:5000',  # Default MLflow URI
                            'registry_uri': None
                        },
                        'is_active': True
                    }
                )
                if created:
                    self.stdout.write(f'Created default connector: {connector.name}')
                else:
                    self.stdout.write(f'Using default connector: {connector.name}')

            if not connector.is_active:
                raise CommandError(f'Connector "{connector.name}" is not active')

            # Sync models based on connector type
            if connector_type == 'mlflow':
                self._sync_mlflow_models(org, connector, dry_run, update_existing)
            else:
                self.stdout.write(self.style.WARNING(f'Syncing for {connector_type} not yet implemented'))

        self.stdout.write(self.style.SUCCESS('Command completed'))

    def _sync_mlflow_models(self, org, connector, dry_run, update_existing):
        """Sync models from MLflow registry."""
        try:
            self.stdout.write('Connecting to MLflow registry...')
            
            # Get models from MLflow
            models_data = sync_models_from_mlflow(connector.config)
            
            self.stdout.write(f'Found {len(models_data)} models in MLflow registry')
            
            if dry_run:
                self.stdout.write(self.style.WARNING('DRY RUN - No models will be created'))
                for model_data in models_data:
                    self.stdout.write(f'  Would sync: {model_data["name"]} v{model_data["version"]}')
                return

            # Sync models to database
            synced_count = 0
            updated_count = 0
            
            with transaction.atomic():
                for model_data in models_data:
                    model_name = model_data['name']
                    model_version = model_data['version']
                    
                    # Check if model already exists
                    existing_model = ModelAsset.objects.filter(
                        organization=org,
                        name=model_name,
                        version=model_version
                    ).first()
                    
                    if existing_model:
                        if update_existing:
                            # Update existing model
                            existing_model.uri = model_data['uri']
                            existing_model.signature = model_data['signature']
                            existing_model.extra = {
                                **existing_model.extra,
                                'metadata': model_data['metadata'],
                                'tags': model_data['tags'],
                                'stage': model_data['stage'],
                                'lineage': model_data['lineage']
                            }
                            existing_model.save()
                            updated_count += 1
                            self.stdout.write(f'Updated: {model_name} v{model_version}')
                        else:
                            self.stdout.write(f'Skipped existing: {model_name} v{model_version}')
                    else:
                        # Create new model asset
                        ModelAsset.objects.create(
                            organization=org,
                            name=model_name,
                            model_type='tabular',  # Default, could be inferred from metadata
                            uri=model_data['uri'],
                            version=model_version,
                            signature=model_data['signature'],
                            extra={
                                'metadata': model_data['metadata'],
                                'tags': model_data['tags'],
                                'stage': model_data['stage'],
                                'lineage': model_data['lineage'],
                                'synced_from': 'mlflow',
                                'connector_id': connector.id
                            }
                        )
                        synced_count += 1
                        self.stdout.write(f'Synced: {model_name} v{model_version}')

            self.stdout.write(self.style.SUCCESS(f'Sync completed: {synced_count} new, {updated_count} updated'))

        except Exception as e:
            raise CommandError(f'Failed to sync MLflow models: {e}')
