from django.core.management.base import BaseCommand
from django.utils import timezone
from users.models import AccountLockout
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Clean up expired account lockouts'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be done without actually doing it',
        )
        parser.add_argument(
            '--older-than',
            type=int,
            default=24,
            help='Remove lockouts older than this many hours (default: 24)',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        older_than_hours = options['older_than']
        
        self.stdout.write(self.style.SUCCESS('Starting expired lockout cleanup...'))
        
        # Calculate cutoff time
        cutoff_time = timezone.now() - timezone.timedelta(hours=older_than_hours)
        
        # Find expired lockouts
        expired_lockouts = AccountLockout.objects.filter(
            expires_at__lt=timezone.now(),
            is_active=True
        )
        
        # Find old inactive lockouts
        old_inactive_lockouts = AccountLockout.objects.filter(
            locked_at__lt=cutoff_time,
            is_active=False
        )
        
        self.stdout.write(f'Found {expired_lockouts.count()} expired active lockouts')
        self.stdout.write(f'Found {old_inactive_lockouts.count()} old inactive lockouts (older than {older_than_hours} hours)')
        
        if dry_run:
            self.stdout.write('[DRY RUN] Would deactivate expired lockouts')
            self.stdout.write('[DRY RUN] Would delete old inactive lockouts')
        else:
            # Deactivate expired lockouts
            expired_count = expired_lockouts.update(is_active=False)
            self.stdout.write(f'Deactivated {expired_count} expired lockouts')
            
            # Delete old inactive lockouts
            deleted_count = old_inactive_lockouts.count()
            old_inactive_lockouts.delete()
            self.stdout.write(f'Deleted {deleted_count} old inactive lockouts')
        
        if dry_run:
            self.stdout.write(self.style.WARNING('DRY RUN - No actual changes made'))
        else:
            self.stdout.write(self.style.SUCCESS('Lockout cleanup completed'))
