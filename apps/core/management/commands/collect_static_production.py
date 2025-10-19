from django.core.management.base import BaseCommand
from django.core.management import call_command
from django.conf import settings
import os
import shutil

class Command(BaseCommand):
    help = 'Collect static files for production deployment'

    def handle(self, *args, **options):
        self.stdout.write('Collecting static files for production...')
        
        # Ensure staticfiles directory exists
        staticfiles_dir = settings.STATIC_ROOT
        if not os.path.exists(staticfiles_dir):
            os.makedirs(staticfiles_dir)
        
        # Collect static files
        call_command('collectstatic', '--noinput', '--clear')
        
        # Copy critical CSS files to ensure they're available
        critical_files = [
            'css/public.css',
            'css/bootstrap.min.css',
            'css/bootstrap-icons.min.css',
            'js/modern-website.js',
            'js/public.js',
            'js/ui-utils.js',
        ]
        
        for file_path in critical_files:
            source = os.path.join(settings.STATIC_ROOT, file_path)
            if os.path.exists(source):
                self.stdout.write(f'✓ {file_path} collected successfully')
            else:
                self.stdout.write(self.style.WARNING(f'⚠ {file_path} not found'))
        
        self.stdout.write(self.style.SUCCESS('Static files collection completed!'))
        self.stdout.write('Make sure to run this command in production after deployment.')
