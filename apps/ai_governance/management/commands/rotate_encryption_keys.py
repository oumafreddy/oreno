"""
Management command to rotate encryption keys for AI governance.
Supports both local and KMS-based key rotation.
"""

from django.core.management.base import BaseCommand, CommandError
from django_tenants.utils import tenant_context
from organizations.models import Organization

from ai_governance.security import key_management_service


class Command(BaseCommand):
    help = 'Rotate encryption keys for AI governance data'

    def add_arguments(self, parser):
        parser.add_argument(
            '--organization',
            type=int,
            help='Organization ID to rotate keys for (optional)'
        )
        parser.add_argument(
            '--all-organizations',
            action='store_true',
            help='Rotate keys for all organizations'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be rotated without actually rotating keys'
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force key rotation even if not due'
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        force = options['force']
        
        if dry_run:
            self.stdout.write(
                self.style.WARNING('DRY RUN MODE - No keys will be rotated')
            )
        
        if options['all_organizations']:
            # Rotate keys for all organizations
            organizations = Organization.objects.all()
            self.stdout.write(f'Rotating keys for {organizations.count()} organizations...')
            
            for org in organizations:
                self._rotate_keys_for_organization(org, dry_run, force)
        elif options['organization']:
            # Rotate keys for specific organization
            try:
                org = Organization.objects.get(id=options['organization'])
                self._rotate_keys_for_organization(org, dry_run, force)
            except Organization.DoesNotExist:
                raise CommandError(f'Organization {options["organization"]} does not exist')
        else:
            # Rotate keys for current tenant context
            self._rotate_keys_for_current_tenant(dry_run, force)

    def _rotate_keys_for_organization(self, organization, dry_run=False, force=False):
        """Rotate keys for a specific organization."""
        self.stdout.write(f'Processing organization: {organization.name}')
        
        with tenant_context(organization):
            if dry_run:
                self.stdout.write(
                    self.style.SUCCESS(f'[DRY RUN] Would rotate keys for {organization.name}')
                )
                return
            
            try:
                # Check if key rotation is due (unless forced)
                if not force and not self._is_key_rotation_due():
                    self.stdout.write(
                        self.style.WARNING(
                            f'Key rotation not due for {organization.name}. Use --force to override.'
                        )
                    )
                    return
                
                # Perform key rotation
                result = key_management_service.rotate_encryption_keys(organization.id)
                
                if result['success']:
                    self.stdout.write(
                        self.style.SUCCESS(
                            f'Successfully rotated keys for {organization.name}'
                        )
                    )
                    if result.get('rotated_keys'):
                        for key in result['rotated_keys']:
                            self.stdout.write(f'  - Rotated key: {key}')
                else:
                    self.stdout.write(
                        self.style.ERROR(
                            f'Failed to rotate keys for {organization.name}: {result.get("error", "Unknown error")}'
                        )
                    )
                    
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(
                        f'Error rotating keys for {organization.name}: {str(e)}'
                    )
                )

    def _rotate_keys_for_current_tenant(self, dry_run=False, force=False):
        """Rotate keys for current tenant context."""
        if dry_run:
            self.stdout.write(
                self.style.SUCCESS('[DRY RUN] Would rotate keys for current tenant')
            )
            return
        
        try:
            # Check if key rotation is due (unless forced)
            if not force and not self._is_key_rotation_due():
                self.stdout.write(
                    self.style.WARNING(
                        'Key rotation not due. Use --force to override.'
                    )
                )
                return
            
            # Perform key rotation
            result = key_management_service.rotate_encryption_keys()
            
            if result['success']:
                self.stdout.write(
                    self.style.SUCCESS('Successfully rotated encryption keys')
                )
                if result.get('rotated_keys'):
                    for key in result['rotated_keys']:
                        self.stdout.write(f'  - Rotated key: {key}')
            else:
                self.stdout.write(
                    self.style.ERROR(
                        f'Failed to rotate keys: {result.get("error", "Unknown error")}'
                    )
                )
                
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error rotating keys: {str(e)}')
            )

    def _is_key_rotation_due(self):
        """Check if key rotation is due based on rotation interval."""
        from django.core.cache import cache
        from django.utils import timezone
        from datetime import timedelta
        
        last_rotation_key = 'ai_governance_last_key_rotation'
        last_rotation = cache.get(last_rotation_key)
        
        if not last_rotation:
            return True  # Never rotated, so it's due
        
        rotation_interval = timedelta(days=key_management_service.rotation_interval_days)
        return timezone.now() - last_rotation > rotation_interval
