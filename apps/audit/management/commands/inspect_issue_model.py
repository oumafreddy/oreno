from django.core.management.base import BaseCommand
from apps.audit.models import Issue

class Command(BaseCommand):
    help = 'Inspects the fields of the Issue model'

    def handle(self, *args, **options):
        self.stdout.write("Fields for apps.audit.models.Issue (Issue._meta.get_fields()):")
        for field in Issue._meta.get_fields():
            self.stdout.write(f"- {field.name} (type: {field.get_internal_type()})")
        
        self.stdout.write("\nLocal Fields for apps.audit.models.Issue (Issue._meta.local_fields):")
        for field in Issue._meta.local_fields:
            self.stdout.write(f"- {field.name} (type: {field.get_internal_type()})")

        self.stdout.write("\nChecking for 'severity_status' specifically:")
        try:
            field = Issue._meta.get_field('severity_status')
            self.stdout.write(f"  Found 'severity_status': {field.name} (type: {field.get_internal_type()})")
        except Exception as e:
            self.stdout.write(f"  'severity_status' not found via get_field: {e}")
