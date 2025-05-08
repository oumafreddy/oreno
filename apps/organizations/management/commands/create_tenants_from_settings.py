from django.core.management.base import BaseCommand
from django.conf import settings
from organizations.models import Organization, Domain
from django.db import transaction

class Command(BaseCommand):
    help = 'Create Organization and Domain objects for each entry in LOCAL_TENANT_DOMAINS.'

    def handle(self, *args, **options):
        created_orgs = 0
        created_domains = 0
        skipped_orgs = 0
        skipped_domains = 0
        with transaction.atomic():
            for domain in getattr(settings, 'LOCAL_TENANT_DOMAINS', []):
                # Use the subdomain as org code and schema_name
                subdomain = domain.split('.')[0]
                org_code = subdomain.upper()
                org_name = subdomain.replace('org', 'Organization ').upper() if subdomain.startswith('org') else subdomain.capitalize()
                schema_name = subdomain.lower()
                # Create or get Organization
                org, org_created = Organization.objects.get_or_create(
                    code=org_code,
                    defaults={
                        'name': org_name,
                        'schema_name': schema_name,
                        'is_active': True,
                    }
                )
                if org_created:
                    created_orgs += 1
                    self.stdout.write(self.style.SUCCESS(f'Created organization: {org.name}'))
                else:
                    skipped_orgs += 1
                # Create or get Domain
                domain_obj, domain_created = Domain.objects.get_or_create(
                    domain=domain,
                    tenant=org,
                    defaults={
                        'is_primary': True
                    }
                )
                if domain_created:
                    created_domains += 1
                    self.stdout.write(self.style.SUCCESS(f'Created domain: {domain} for {org.name}'))
                else:
                    skipped_domains += 1
        self.stdout.write(self.style.SUCCESS(f'Organizations created: {created_orgs}, skipped: {skipped_orgs}'))
        self.stdout.write(self.style.SUCCESS(f'Domains created: {created_domains}, skipped: {skipped_domains}')) 