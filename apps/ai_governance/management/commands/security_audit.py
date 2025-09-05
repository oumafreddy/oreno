# oreno/apps/ai_governance/management/commands/security_audit.py

from django.core.management.base import BaseCommand, CommandError
from django_tenants.utils import tenant_context
from django.utils import timezone
import json
import logging

from organizations.models import Organization
from ai_governance.security import security_audit_service

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Conduct security audit of AI governance system'

    def add_arguments(self, parser):
        parser.add_argument(
            '--organization',
            type=int,
            help='Organization ID to audit (required)',
            required=True
        )
        parser.add_argument(
            '--output-format',
            choices=['json', 'text', 'csv'],
            default='json',
            help='Output format for audit results'
        )
        parser.add_argument(
            '--output-file',
            type=str,
            help='Output file path (if not specified, prints to stdout)'
        )
        parser.add_argument(
            '--include-recommendations',
            action='store_true',
            help='Include detailed recommendations in output'
        )
        parser.add_argument(
            '--severity-filter',
            choices=['critical', 'high', 'medium', 'low', 'info'],
            help='Filter findings by minimum severity level'
        )

    def handle(self, *args, **options):
        organization_id = options['organization']
        output_format = options['output_format']
        output_file = options.get('output_file')
        include_recommendations = options['include_recommendations']
        severity_filter = options.get('severity_filter')

        try:
            # Get organization
            try:
                org = Organization.objects.get(id=organization_id)
            except Organization.DoesNotExist:
                raise CommandError(f'Organization with ID {organization_id} not found')

            self.stdout.write(
                self.style.SUCCESS(f'Starting security audit for organization: {org.name}')
            )

            # Run security audit within tenant context
            with tenant_context(org):
                audit_results = security_audit_service.conduct_security_audit(organization_id)

                # Filter findings by severity if specified
                if severity_filter:
                    severity_levels = ['critical', 'high', 'medium', 'low', 'info']
                    min_severity_index = severity_levels.index(severity_filter)
                    filtered_findings = [
                        finding for finding in audit_results['findings']
                        if severity_levels.index(finding['severity']) >= min_severity_index
                    ]
                    audit_results['findings'] = filtered_findings

                # Format output
                if output_format == 'json':
                    output_content = self._format_json_output(audit_results, include_recommendations)
                elif output_format == 'text':
                    output_content = self._format_text_output(audit_results, include_recommendations)
                elif output_format == 'csv':
                    output_content = self._format_csv_output(audit_results, include_recommendations)

                # Write output
                if output_file:
                    with open(output_file, 'w') as f:
                        f.write(output_content)
                    self.stdout.write(
                        self.style.SUCCESS(f'Audit results written to: {output_file}')
                    )
                else:
                    self.stdout.write(output_content)

                # Print summary
                self._print_audit_summary(audit_results)

        except Exception as e:
            logger.error(f"Security audit failed: {e}")
            raise CommandError(f'Security audit failed: {e}')

    def _format_json_output(self, audit_results, include_recommendations):
        """Format audit results as JSON."""
        output_data = {
            'audit_summary': {
                'organization_id': audit_results['organization_id'],
                'audit_date': audit_results['audit_date'],
                'security_score': audit_results['security_score'],
                'overall_status': audit_results['overall_status'],
                'total_findings': len(audit_results['findings']),
                'critical_findings': sum(1 for f in audit_results['findings'] if f['severity'] == 'critical'),
                'high_findings': sum(1 for f in audit_results['findings'] if f['severity'] == 'high'),
            },
            'findings': audit_results['findings'],
            'compliance_status': audit_results['compliance_status']
        }

        if include_recommendations:
            output_data['recommendations'] = audit_results['recommendations']

        return json.dumps(output_data, indent=2, default=str)

    def _format_text_output(self, audit_results, include_recommendations):
        """Format audit results as human-readable text."""
        lines = []
        lines.append("=" * 80)
        lines.append("AI GOVERNANCE SECURITY AUDIT REPORT")
        lines.append("=" * 80)
        lines.append(f"Organization ID: {audit_results['organization_id']}")
        lines.append(f"Audit Date: {audit_results['audit_date']}")
        lines.append(f"Security Score: {audit_results['security_score']}/100")
        lines.append(f"Overall Status: {audit_results['overall_status'].upper()}")
        lines.append("")

        # Findings summary
        lines.append("FINDINGS SUMMARY")
        lines.append("-" * 40)
        findings_by_severity = {}
        for finding in audit_results['findings']:
            severity = finding['severity']
            findings_by_severity[severity] = findings_by_severity.get(severity, 0) + 1

        for severity in ['critical', 'high', 'medium', 'low', 'info']:
            count = findings_by_severity.get(severity, 0)
            lines.append(f"{severity.upper()}: {count}")

        lines.append("")

        # Detailed findings
        lines.append("DETAILED FINDINGS")
        lines.append("-" * 40)
        for i, finding in enumerate(audit_results['findings'], 1):
            lines.append(f"{i}. [{finding['severity'].upper()}] {finding['category']}")
            lines.append(f"   Description: {finding['description']}")
            lines.append(f"   Status: {finding['status']}")
            if 'details' in finding:
                lines.append(f"   Details: {finding['details']}")
            lines.append("")

        # Compliance status
        lines.append("COMPLIANCE STATUS")
        lines.append("-" * 40)
        for framework, status in audit_results['compliance_status'].items():
            lines.append(f"{framework.upper()}:")
            if isinstance(status, dict):
                if 'compliance_score' in status:
                    lines.append(f"  Score: {status['compliance_score']}/100")
                if 'overall_status' in status:
                    lines.append(f"  Status: {status['overall_status']}")
            lines.append("")

        # Recommendations
        if include_recommendations and audit_results['recommendations']:
            lines.append("RECOMMENDATIONS")
            lines.append("-" * 40)
            for i, recommendation in enumerate(audit_results['recommendations'], 1):
                lines.append(f"{i}. {recommendation}")
            lines.append("")

        lines.append("=" * 80)
        return "\n".join(lines)

    def _format_csv_output(self, audit_results, include_recommendations):
        """Format audit results as CSV."""
        import csv
        import io

        output = io.StringIO()
        writer = csv.writer(output)

        # Write header
        writer.writerow([
            'Organization ID', 'Audit Date', 'Security Score', 'Overall Status',
            'Finding Category', 'Severity', 'Description', 'Status'
        ])

        # Write findings
        for finding in audit_results['findings']:
            writer.writerow([
                audit_results['organization_id'],
                audit_results['audit_date'],
                audit_results['security_score'],
                audit_results['overall_status'],
                finding['category'],
                finding['severity'],
                finding['description'],
                finding['status']
            ])

        return output.getvalue()

    def _print_audit_summary(self, audit_results):
        """Print audit summary to console."""
        self.stdout.write("")
        self.stdout.write(self.style.SUCCESS("AUDIT COMPLETED"))
        self.stdout.write("-" * 40)
        self.stdout.write(f"Security Score: {audit_results['security_score']}/100")
        self.stdout.write(f"Overall Status: {audit_results['overall_status'].upper()}")
        
        # Count findings by severity
        findings_by_severity = {}
        for finding in audit_results['findings']:
            severity = finding['severity']
            findings_by_severity[severity] = findings_by_severity.get(severity, 0) + 1

        self.stdout.write("Findings Summary:")
        for severity in ['critical', 'high', 'medium', 'low', 'info']:
            count = findings_by_severity.get(severity, 0)
            if count > 0:
                style = self.style.ERROR if severity in ['critical', 'high'] else self.style.WARNING
                self.stdout.write(style(f"  {severity.upper()}: {count}"))

        # Compliance status
        self.stdout.write("Compliance Status:")
        for framework, status in audit_results['compliance_status'].items():
            if isinstance(status, dict) and 'compliance_score' in status:
                score = status['compliance_score']
                style = self.style.SUCCESS if score >= 80 else self.style.WARNING
                self.stdout.write(style(f"  {framework.upper()}: {score}/100"))

        self.stdout.write("")
