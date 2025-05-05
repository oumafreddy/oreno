from django.core.management.base import BaseCommand
from organizations.models import Organization, OrganizationSettings
from django.db import transaction

class Command(BaseCommand):
    help = 'Create OrganizationSettings for all organizations that do not have one.'

    def handle(self, *args, **options):
        created_count = 0
        with transaction.atomic():
            for org in Organization.objects.all():
                settings_obj, created = OrganizationSettings.objects.get_or_create(organization=org)
                if created:
                    created_count += 1
                    self.stdout.write(self.style.SUCCESS(f'Created OrganizationSettings for: {org.name}'))
        if created_count == 0:
            self.stdout.write(self.style.NOTICE('All organizations already have settings.'))
        else:
            self.stdout.write(self.style.SUCCESS(f'Created settings for {created_count} organizations.')) 