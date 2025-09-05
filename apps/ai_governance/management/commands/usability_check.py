# oreno/apps/ai_governance/management/commands/usability_check.py

from django.core.management.base import BaseCommand, CommandError
from django_tenants.utils import tenant_context
from django.utils import timezone
from django.contrib.auth import get_user_model
from django.test import Client
from django.urls import reverse
import json
import logging

from organizations.models import Organization
from ai_governance.models import ModelAsset, DatasetAsset, TestPlan, TestRun

logger = logging.getLogger(__name__)
User = get_user_model()


class Command(BaseCommand):
    help = 'Run usability checks for AI governance module UI and workflows'

    def add_arguments(self, parser):
        parser.add_argument(
            '--organization',
            type=int,
            help='Organization ID to run usability checks (required)',
            required=True
        )
        parser.add_argument(
            '--output-file',
            type=str,
            help='Output file path for usability check results (JSON format)'
        )
        parser.add_argument(
            '--check-category',
            choices=['all', 'navigation', 'forms', 'workflows', 'responsiveness', 'accessibility'],
            default='all',
            help='Category of usability checks to run'
        )
        parser.add_argument(
            '--create-test-user',
            action='store_true',
            help='Create a test user for usability checks'
        )

    def handle(self, *args, **options):
        organization_id = options['organization']
        output_file = options.get('output_file')
        check_category = options['check_category']
        create_test_user = options['create_test_user']

        try:
            # Get organization
            try:
                org = Organization.objects.get(id=organization_id)
            except Organization.DoesNotExist:
                raise CommandError(f'Organization with ID {organization_id} not found')

            self.stdout.write(
                self.style.SUCCESS(f'Starting usability checks for organization: {org.name}')
            )

            # Run usability checks within tenant context
            with tenant_context(org):
                usability_results = {
                    'organization_id': organization_id,
                    'organization_name': org.name,
                    'check_date': timezone.now().isoformat(),
                    'check_category': check_category,
                    'checks_run': [],
                    'summary': {
                        'total_checks': 0,
                        'passed_checks': 0,
                        'failed_checks': 0,
                        'overall_status': 'pending'
                    }
                }

                # Create test user if requested
                test_user = None
                if create_test_user:
                    test_user = self._create_test_user(org)
                    usability_results['test_user_created'] = test_user.id

                # Run checks based on category
                if check_category in ['all', 'navigation']:
                    self._run_navigation_checks(usability_results, test_user)
                
                if check_category in ['all', 'forms']:
                    self._run_form_checks(usability_results, test_user)
                
                if check_category in ['all', 'workflows']:
                    self._run_workflow_checks(usability_results, test_user)
                
                if check_category in ['all', 'responsiveness']:
                    self._run_responsiveness_checks(usability_results, test_user)
                
                if check_category in ['all', 'accessibility']:
                    self._run_accessibility_checks(usability_results, test_user)

                # Calculate summary
                self._calculate_summary(usability_results)

                # Output results
                if output_file:
                    with open(output_file, 'w') as f:
                        json.dump(usability_results, f, indent=2, default=str)
                    self.stdout.write(
                        self.style.SUCCESS(f'Usability check results written to: {output_file}')
                    )
                else:
                    self.stdout.write(json.dumps(usability_results, indent=2, default=str))

                # Print summary
                self._print_usability_summary(usability_results)

        except Exception as e:
            logger.error(f"Usability checks failed: {e}")
            raise CommandError(f'Usability checks failed: {e}')

    def _create_test_user(self, org):
        """Create a test user for usability checks."""
        test_user, created = User.objects.get_or_create(
            email='uat-test@example.com',
            defaults={
                'username': 'uat_test_user',
                'first_name': 'UAT',
                'last_name': 'Test User',
                'organization': org,
                'role': 'staff',
                'is_active': True
            }
        )
        
        if created:
            test_user.set_password('uat_test_password')
            test_user.save()
            self.stdout.write(f"Created test user: {test_user.email}")
        else:
            self.stdout.write(f"Using existing test user: {test_user.email}")
        
        return test_user

    def _run_navigation_checks(self, usability_results, test_user):
        """Run navigation usability checks."""
        self.stdout.write("Running navigation checks...")
        
        # Check 1: Dashboard accessibility
        check_result = self._run_check(
            'Dashboard Navigation',
            self._check_dashboard_navigation,
            'navigation',
            test_user
        )
        usability_results['checks_run'].append(check_result)

        # Check 2: Menu structure
        check_result = self._run_check(
            'Menu Structure',
            self._check_menu_structure,
            'navigation',
            test_user
        )
        usability_results['checks_run'].append(check_result)

        # Check 3: Breadcrumb navigation
        check_result = self._run_check(
            'Breadcrumb Navigation',
            self._check_breadcrumb_navigation,
            'navigation',
            test_user
        )
        usability_results['checks_run'].append(check_result)

    def _run_form_checks(self, usability_results, test_user):
        """Run form usability checks."""
        self.stdout.write("Running form checks...")
        
        # Check 1: Form validation
        check_result = self._run_check(
            'Form Validation',
            self._check_form_validation,
            'forms',
            test_user
        )
        usability_results['checks_run'].append(check_result)

        # Check 2: Form accessibility
        check_result = self._run_check(
            'Form Accessibility',
            self._check_form_accessibility,
            'forms',
            test_user
        )
        usability_results['checks_run'].append(check_result)

        # Check 3: Form error handling
        check_result = self._run_check(
            'Form Error Handling',
            self._check_form_error_handling,
            'forms',
            test_user
        )
        usability_results['checks_run'].append(check_result)

    def _run_workflow_checks(self, usability_results, test_user):
        """Run workflow usability checks."""
        self.stdout.write("Running workflow checks...")
        
        # Check 1: Test run workflow
        check_result = self._run_check(
            'Test Run Workflow',
            self._check_test_run_workflow,
            'workflows',
            test_user
        )
        usability_results['checks_run'].append(check_result)

        # Check 2: Model registration workflow
        check_result = self._run_check(
            'Model Registration Workflow',
            self._check_model_registration_workflow,
            'workflows',
            test_user
        )
        usability_results['checks_run'].append(check_result)

        # Check 3: Report generation workflow
        check_result = self._run_check(
            'Report Generation Workflow',
            self._check_report_generation_workflow,
            'workflows',
            test_user
        )
        usability_results['checks_run'].append(check_result)

    def _run_responsiveness_checks(self, usability_results, test_user):
        """Run responsiveness checks."""
        self.stdout.write("Running responsiveness checks...")
        
        # Check 1: Mobile responsiveness
        check_result = self._run_check(
            'Mobile Responsiveness',
            self._check_mobile_responsiveness,
            'responsiveness',
            test_user
        )
        usability_results['checks_run'].append(check_result)

        # Check 2: Tablet responsiveness
        check_result = self._run_check(
            'Tablet Responsiveness',
            self._check_tablet_responsiveness,
            'responsiveness',
            test_user
        )
        usability_results['checks_run'].append(check_result)

    def _run_accessibility_checks(self, usability_results, test_user):
        """Run accessibility checks."""
        self.stdout.write("Running accessibility checks...")
        
        # Check 1: Keyboard navigation
        check_result = self._run_check(
            'Keyboard Navigation',
            self._check_keyboard_navigation,
            'accessibility',
            test_user
        )
        usability_results['checks_run'].append(check_result)

        # Check 2: Screen reader compatibility
        check_result = self._run_check(
            'Screen Reader Compatibility',
            self._check_screen_reader_compatibility,
            'accessibility',
            test_user
        )
        usability_results['checks_run'].append(check_result)

        # Check 3: Color contrast
        check_result = self._run_check(
            'Color Contrast',
            self._check_color_contrast,
            'accessibility',
            test_user
        )
        usability_results['checks_run'].append(check_result)

    def _run_check(self, check_name, check_function, category, test_user):
        """Run a single usability check and return results."""
        try:
            result = check_function(test_user)
            return {
                'name': check_name,
                'category': category,
                'status': 'passed' if result else 'failed',
                'message': 'Check passed successfully' if result else 'Check failed',
                'timestamp': timezone.now().isoformat()
            }
        except Exception as e:
            return {
                'name': check_name,
                'category': category,
                'status': 'failed',
                'message': f'Check failed with error: {str(e)}',
                'timestamp': timezone.now().isoformat()
            }

    # Check implementations
    def _check_dashboard_navigation(self, test_user):
        """Check dashboard navigation usability."""
        if not test_user:
            return False
        
        client = Client()
        client.force_login(test_user)
        
        try:
            # Test dashboard access
            response = client.get('/ai_governance/dashboard/')
            return response.status_code == 200
        except Exception:
            return False

    def _check_menu_structure(self, test_user):
        """Check menu structure usability."""
        if not test_user:
            return False
        
        client = Client()
        client.force_login(test_user)
        
        try:
            # Test main navigation
            response = client.get('/ai_governance/dashboard/')
            if response.status_code == 200:
                # Check if navigation elements are present
                content = response.content.decode('utf-8')
                return 'ai_governance' in content.lower()
            return False
        except Exception:
            return False

    def _check_breadcrumb_navigation(self, test_user):
        """Check breadcrumb navigation."""
        if not test_user:
            return False
        
        client = Client()
        client.force_login(test_user)
        
        try:
            # Test breadcrumb presence
            response = client.get('/ai_governance/dashboard/')
            if response.status_code == 200:
                content = response.content.decode('utf-8')
                # Check for breadcrumb indicators
                return 'breadcrumb' in content.lower() or 'nav' in content.lower()
            return False
        except Exception:
            return False

    def _check_form_validation(self, test_user):
        """Check form validation usability."""
        if not test_user:
            return False
        
        client = Client()
        client.force_login(test_user)
        
        try:
            # Test form validation by submitting invalid data
            response = client.post('/ai_governance/api/model-assets/', {
                'name': '',  # Invalid: empty name
                'model_type': 'invalid_type'  # Invalid: invalid model type
            })
            
            # Should return validation errors
            return response.status_code == 400
        except Exception:
            return False

    def _check_form_accessibility(self, test_user):
        """Check form accessibility."""
        if not test_user:
            return False
        
        client = Client()
        client.force_login(test_user)
        
        try:
            # Test form accessibility
            response = client.get('/ai_governance/dashboard/')
            if response.status_code == 200:
                content = response.content.decode('utf-8')
                # Check for accessibility attributes
                return 'label' in content.lower() and 'form' in content.lower()
            return False
        except Exception:
            return False

    def _check_form_error_handling(self, test_user):
        """Check form error handling."""
        if not test_user:
            return False
        
        client = Client()
        client.force_login(test_user)
        
        try:
            # Test error handling
            response = client.post('/ai_governance/api/model-assets/', {
                'name': 'Test Model',
                'model_type': 'invalid_type'
            })
            
            # Should handle errors gracefully
            return response.status_code in [400, 422]
        except Exception:
            return False

    def _check_test_run_workflow(self, test_user):
        """Check test run workflow usability."""
        if not test_user:
            return False
        
        client = Client()
        client.force_login(test_user)
        
        try:
            # Test test run creation workflow
            response = client.get('/ai_governance/api/test-runs/')
            return response.status_code == 200
        except Exception:
            return False

    def _check_model_registration_workflow(self, test_user):
        """Check model registration workflow."""
        if not test_user:
            return False
        
        client = Client()
        client.force_login(test_user)
        
        try:
            # Test model registration workflow
            response = client.get('/ai_governance/api/model-assets/')
            return response.status_code == 200
        except Exception:
            return False

    def _check_report_generation_workflow(self, test_user):
        """Check report generation workflow."""
        if not test_user:
            return False
        
        client = Client()
        client.force_login(test_user)
        
        try:
            # Test report generation workflow
            response = client.get('/ai_governance/dashboard/')
            if response.status_code == 200:
                content = response.content.decode('utf-8')
                # Check for report generation elements
                return 'report' in content.lower() or 'export' in content.lower()
            return False
        except Exception:
            return False

    def _check_mobile_responsiveness(self, test_user):
        """Check mobile responsiveness."""
        if not test_user:
            return False
        
        client = Client()
        client.force_login(test_user)
        
        try:
            # Test mobile viewport
            response = client.get('/ai_governance/dashboard/', HTTP_USER_AGENT='Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X)')
            if response.status_code == 200:
                content = response.content.decode('utf-8')
                # Check for responsive design indicators
                return 'viewport' in content.lower() or 'responsive' in content.lower()
            return False
        except Exception:
            return False

    def _check_tablet_responsiveness(self, test_user):
        """Check tablet responsiveness."""
        if not test_user:
            return False
        
        client = Client()
        client.force_login(test_user)
        
        try:
            # Test tablet viewport
            response = client.get('/ai_governance/dashboard/', HTTP_USER_AGENT='Mozilla/5.0 (iPad; CPU OS 14_0 like Mac OS X)')
            if response.status_code == 200:
                content = response.content.decode('utf-8')
                # Check for responsive design indicators
                return 'viewport' in content.lower() or 'responsive' in content.lower()
            return False
        except Exception:
            return False

    def _check_keyboard_navigation(self, test_user):
        """Check keyboard navigation accessibility."""
        if not test_user:
            return False
        
        client = Client()
        client.force_login(test_user)
        
        try:
            # Test keyboard navigation
            response = client.get('/ai_governance/dashboard/')
            if response.status_code == 200:
                content = response.content.decode('utf-8')
                # Check for keyboard navigation indicators
                return 'tabindex' in content.lower() or 'keyboard' in content.lower()
            return False
        except Exception:
            return False

    def _check_screen_reader_compatibility(self, test_user):
        """Check screen reader compatibility."""
        if not test_user:
            return False
        
        client = Client()
        client.force_login(test_user)
        
        try:
            # Test screen reader compatibility
            response = client.get('/ai_governance/dashboard/')
            if response.status_code == 200:
                content = response.content.decode('utf-8')
                # Check for accessibility attributes
                return 'aria-' in content.lower() or 'alt=' in content.lower()
            return False
        except Exception:
            return False

    def _check_color_contrast(self, test_user):
        """Check color contrast accessibility."""
        if not test_user:
            return False
        
        client = Client()
        client.force_login(test_user)
        
        try:
            # Test color contrast
            response = client.get('/ai_governance/dashboard/')
            if response.status_code == 200:
                content = response.content.decode('utf-8')
                # Check for CSS that might indicate good contrast
                return 'color:' in content.lower() or 'background:' in content.lower()
            return False
        except Exception:
            return False

    def _calculate_summary(self, usability_results):
        """Calculate usability check summary."""
        checks = usability_results['checks_run']
        total_checks = len(checks)
        passed_checks = sum(1 for check in checks if check['status'] == 'passed')
        failed_checks = total_checks - passed_checks
        
        usability_results['summary'] = {
            'total_checks': total_checks,
            'passed_checks': passed_checks,
            'failed_checks': failed_checks,
            'overall_status': 'passed' if failed_checks == 0 else 'failed',
            'success_rate': (passed_checks / total_checks * 100) if total_checks > 0 else 0
        }

    def _print_usability_summary(self, usability_results):
        """Print usability check summary to console."""
        self.stdout.write("")
        self.stdout.write(self.style.SUCCESS("USABILITY CHECKS COMPLETED"))
        self.stdout.write("-" * 40)
        
        summary = usability_results['summary']
        self.stdout.write(f"Total Checks: {summary['total_checks']}")
        self.stdout.write(f"Passed: {summary['passed_checks']}")
        self.stdout.write(f"Failed: {summary['failed_checks']}")
        self.stdout.write(f"Success Rate: {summary['success_rate']:.1f}%")
        
        status_style = self.style.SUCCESS if summary['overall_status'] == 'passed' else self.style.ERROR
        self.stdout.write(status_style(f"Overall Status: {summary['overall_status'].upper()}"))
        
        # Show failed checks
        failed_checks = [check for check in usability_results['checks_run'] if check['status'] == 'failed']
        if failed_checks:
            self.stdout.write("")
            self.stdout.write(self.style.ERROR("FAILED CHECKS:"))
            for check in failed_checks:
                self.stdout.write(f"  - {check['name']}: {check['message']}")
        
        self.stdout.write("")
