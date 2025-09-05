"""
Management command to monitor AI governance performance and generate reports.
Follows the same pattern as other management commands in the project.
"""

from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
from django_tenants.utils import tenant_context
from organizations.models import Organization
from datetime import timedelta

from ai_governance.performance import MetricsCollector, performance_monitor
from ai_governance.alerts import slo_monitor, alert_manager


class Command(BaseCommand):
    help = 'Monitor AI governance performance and generate reports'

    def add_arguments(self, parser):
        parser.add_argument(
            '--organization',
            type=int,
            help='Organization ID to monitor (optional, defaults to all)'
        )
        parser.add_argument(
            '--report-type',
            type=str,
            choices=['performance', 'slo', 'alerts', 'all'],
            default='all',
            help='Type of report to generate (default: all)'
        )
        parser.add_argument(
            '--output-format',
            type=str,
            choices=['json', 'text', 'csv'],
            default='text',
            help='Output format for the report (default: text)'
        )
        parser.add_argument(
            '--save-to-file',
            type=str,
            help='Save report to file (optional)'
        )

    def handle(self, *args, **options):
        org_id = options.get('organization')
        report_type = options['report_type']
        output_format = options['output_format']
        save_to_file = options.get('save_to_file')

        # Get organizations to monitor
        if org_id:
            try:
                organizations = [Organization.objects.get(id=org_id)]
            except Organization.DoesNotExist:
                raise CommandError(f'Organization with ID {org_id} not found')
        else:
            organizations = Organization.objects.all()

        if not organizations:
            self.stdout.write(
                self.style.WARNING('No organizations found to monitor')
            )
            return

        # Generate reports for each organization
        all_reports = {}
        
        for org in organizations:
            self.stdout.write(f'Monitoring organization: {org.name}')
            
            with tenant_context(org):
                org_report = self._generate_organization_report(org, report_type)
                all_reports[org.name] = org_report

        # Output reports
        if output_format == 'json':
            self._output_json_report(all_reports, save_to_file)
        elif output_format == 'csv':
            self._output_csv_report(all_reports, save_to_file)
        else:
            self._output_text_report(all_reports, save_to_file)

        self.stdout.write(self.style.SUCCESS('Performance monitoring completed'))

    def _generate_organization_report(self, org, report_type):
        """Generate performance report for an organization."""
        report = {
            'organization': org.name,
            'timestamp': timezone.now().isoformat(),
            'reports': {}
        }

        if report_type in ['performance', 'all']:
            report['reports']['performance'] = self._generate_performance_report(org)
        
        if report_type in ['slo', 'all']:
            report['reports']['slo'] = self._generate_slo_report(org)
        
        if report_type in ['alerts', 'all']:
            report['reports']['alerts'] = self._generate_alerts_report(org)

        return report

    def _generate_performance_report(self, org):
        """Generate performance metrics report."""
        metrics_collector = MetricsCollector(org.id)
        
        return {
            'dashboard_metrics': metrics_collector.get_dashboard_metrics(),
            'test_performance': metrics_collector.get_test_performance_metrics(),
            'compliance_metrics': metrics_collector.get_compliance_metrics()
        }

    def _generate_slo_report(self, org):
        """Generate SLO compliance report."""
        return slo_monitor.get_slo_metrics(org.id)

    def _generate_alerts_report(self, org):
        """Generate alerts summary report."""
        from .models import TestRun, TestResult
        
        # Get recent test runs with issues
        recent_runs = TestRun.objects.filter(
            organization=org,
            created_at__gte=timezone.now() - timedelta(days=7)
        )
        
        failed_runs = recent_runs.filter(status='failed')
        failed_tests = TestResult.objects.filter(
            test_run__organization=org,
            passed=False,
            created_at__gte=timezone.now() - timedelta(days=7)
        )
        
        return {
            'total_runs': recent_runs.count(),
            'failed_runs': failed_runs.count(),
            'failed_tests': failed_tests.count(),
            'success_rate': ((recent_runs.count() - failed_runs.count()) / recent_runs.count() * 100) if recent_runs.count() > 0 else 0,
            'recent_failures': [
                {
                    'test_run_id': run.id,
                    'model_name': run.model_asset.name,
                    'status': run.status,
                    'error_message': run.error_message,
                    'created_at': run.created_at.isoformat()
                }
                for run in failed_runs[:10]  # Last 10 failures
            ]
        }

    def _output_text_report(self, reports, save_to_file):
        """Output report in text format."""
        output_lines = []
        
        for org_name, report in reports.items():
            output_lines.append(f"\n{'='*60}")
            output_lines.append(f"AI GOVERNANCE PERFORMANCE REPORT")
            output_lines.append(f"Organization: {org_name}")
            output_lines.append(f"Generated: {report['timestamp']}")
            output_lines.append(f"{'='*60}")
            
            if 'performance' in report['reports']:
                perf = report['reports']['performance']
                output_lines.append(f"\nPERFORMANCE METRICS:")
                output_lines.append(f"  Total Models: {perf['dashboard_metrics'].get('total_models', 0)}")
                output_lines.append(f"  Total Test Runs: {perf['dashboard_metrics'].get('total_test_runs', 0)}")
                output_lines.append(f"  Recent Test Runs: {perf['dashboard_metrics'].get('recent_test_runs', 0)}")
                output_lines.append(f"  Average Execution Time: {perf['test_performance'].get('avg_execution_time', 0):.2f}s")
                output_lines.append(f"  Success Rate: {perf['test_performance'].get('success_rate', 0):.1f}%")
            
            if 'slo' in report['reports']:
                slo = report['reports']['slo']
                output_lines.append(f"\nSLO COMPLIANCE:")
                if 'slo_status' in slo:
                    for slo_name, slo_data in slo['slo_status'].items():
                        if isinstance(slo_data, dict) and 'compliant' in slo_data:
                            status = "✓" if slo_data['compliant'] else "✗"
                            output_lines.append(f"  {status} {slo_name}: {slo_data.get('current', 0):.1f} (target: {slo_data.get('target', 0)})")
            
            if 'alerts' in report['reports']:
                alerts = report['reports']['alerts']
                output_lines.append(f"\nALERTS SUMMARY:")
                output_lines.append(f"  Total Runs: {alerts.get('total_runs', 0)}")
                output_lines.append(f"  Failed Runs: {alerts.get('failed_runs', 0)}")
                output_lines.append(f"  Success Rate: {alerts.get('success_rate', 0):.1f}%")
                
                if alerts.get('recent_failures'):
                    output_lines.append(f"\n  Recent Failures:")
                    for failure in alerts['recent_failures'][:5]:
                        output_lines.append(f"    - {failure['model_name']} (Run {failure['test_run_id']}): {failure['error_message'][:50]}...")
        
        output_text = '\n'.join(output_lines)
        
        if save_to_file:
            with open(save_to_file, 'w') as f:
                f.write(output_text)
            self.stdout.write(f'Report saved to: {save_to_file}')
        else:
            self.stdout.write(output_text)

    def _output_json_report(self, reports, save_to_file):
        """Output report in JSON format."""
        import json
        
        output_json = json.dumps(reports, indent=2, default=str)
        
        if save_to_file:
            with open(save_to_file, 'w') as f:
                f.write(output_json)
            self.stdout.write(f'JSON report saved to: {save_to_file}')
        else:
            self.stdout.write(output_json)

    def _output_csv_report(self, reports, save_to_file):
        """Output report in CSV format."""
        import csv
        
        if save_to_file:
            with open(save_to_file, 'w', newline='') as f:
                writer = csv.writer(f)
                
                # Write header
                writer.writerow([
                    'Organization', 'Timestamp', 'Total Models', 'Total Test Runs',
                    'Recent Test Runs', 'Avg Execution Time', 'Success Rate',
                    'SLO Compliance', 'Failed Runs', 'Failed Tests'
                ])
                
                # Write data
                for org_name, report in reports.items():
                    perf = report['reports'].get('performance', {})
                    slo = report['reports'].get('slo', {})
                    alerts = report['reports'].get('alerts', {})
                    
                    slo_compliance = 0
                    if 'slo_status' in slo and 'overall_compliance' in slo['slo_status']:
                        slo_compliance = slo['slo_status']['overall_compliance'].get('compliance_percentage', 0)
                    
                    writer.writerow([
                        org_name,
                        report['timestamp'],
                        perf.get('dashboard_metrics', {}).get('total_models', 0),
                        perf.get('dashboard_metrics', {}).get('total_test_runs', 0),
                        perf.get('dashboard_metrics', {}).get('recent_test_runs', 0),
                        perf.get('test_performance', {}).get('avg_execution_time', 0),
                        perf.get('test_performance', {}).get('success_rate', 0),
                        slo_compliance,
                        alerts.get('failed_runs', 0),
                        alerts.get('failed_tests', 0)
                    ])
            
            self.stdout.write(f'CSV report saved to: {save_to_file}')
        else:
            self.stdout.write(self.style.WARNING('CSV output requires --save-to-file option'))
