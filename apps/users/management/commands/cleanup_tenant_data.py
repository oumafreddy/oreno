import sys
from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth import get_user_model
from django_tenants.utils import get_tenant_model, tenant_context
from django.utils import timezone
from datetime import datetime
from audit.models import Approval, Engagement, Issue, AuditWorkplan
from users.models import CustomUser
from organizations.models import Organization
from django.db.models import Q

class Command(BaseCommand):
    help = 'Anonymize or delete tenant data for users or organizations. Supports filtering by user, organization, and date.'

    def add_arguments(self, parser):
        parser.add_argument('--user', type=str, help='User email or ID to target')
        parser.add_argument('--organization', type=str, help='Organization code or ID to target')
        parser.add_argument('--before', type=str, help='Only affect data before this date (YYYY-MM-DD)')
        parser.add_argument('--anonymize', action='store_true', help='Anonymize data instead of deleting')
        parser.add_argument('--delete', action='store_true', help='Delete data instead of anonymizing')

    def handle(self, *args, **options):
        user_filter = options.get('user')
        org_filter = options.get('organization')
        before = options.get('before')
        anonymize = options.get('anonymize')
        delete = options.get('delete')

        if not (anonymize or delete):
            self.stdout.write(self.style.ERROR('Specify either --anonymize or --delete'))
            sys.exit(1)
        if anonymize and delete:
            self.stdout.write(self.style.ERROR('Choose only one: --anonymize or --delete'))
            sys.exit(1)

        # Parse date
        before_date = None
        if before:
            try:
                before_date = datetime.strptime(before, '%Y-%m-%d').date()
            except ValueError:
                raise CommandError('Invalid date format for --before. Use YYYY-MM-DD.')

        # Find organizations
        org_qs = Organization.objects.all()
        if org_filter:
            if org_filter.isdigit():
                org_qs = org_qs.filter(pk=int(org_filter))
            else:
                org_qs = org_qs.filter(code=org_filter)
        if not org_qs.exists():
            self.stdout.write(self.style.WARNING('No organizations found matching filter.'))
            return

        for org in org_qs:
            self.stdout.write(self.style.NOTICE(f'Processing tenant: {org}'))
            with tenant_context(org):
                user_qs = CustomUser.objects.all()
                if user_filter:
                    if user_filter.isdigit():
                        user_qs = user_qs.filter(pk=int(user_filter))
                    else:
                        user_qs = user_qs.filter(email=user_filter)
                if before_date:
                    user_qs = user_qs.filter(date_joined__lt=before_date)
                for user in user_qs:
                    self.stdout.write(f'  Cleaning data for user: {user.email}')
                    if anonymize:
                        Approval.objects.filter(Q(requester=user) | Q(approver=user)).update(requester=None, approver=None, comments='[ANONYMIZED]')
                        Engagement.objects.filter(assigned_to=user).update(assigned_to=None)
                        Issue.objects.filter(issue_owner=user).update(issue_owner=None, issue_owner_title='[ANONYMIZED]')
                        AuditWorkplan.objects.filter(created_by=user).update(created_by=None)
                        self.stdout.write(self.style.SUCCESS(f'    Anonymized data for user {user.email}'))
                    elif delete:
                        Approval.objects.filter(Q(requester=user) | Q(approver=user)).delete()
                        Engagement.objects.filter(assigned_to=user).delete()
                        Issue.objects.filter(issue_owner=user).delete()
                        AuditWorkplan.objects.filter(created_by=user).delete()
                        self.stdout.write(self.style.SUCCESS(f'    Deleted data for user {user.email}'))
            self.stdout.write(self.style.SUCCESS(f'Finished processing tenant: {org}')) 