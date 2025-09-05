# oreno/apps/ai_governance/management/commands/gdpr_compliance_check.py

from django.core.management.base import BaseCommand, CommandError
from django_tenants.utils import tenant_context
from django.utils import timezone
import json
import logging

from organizations.models import Organization
from ai_governance.security import gdpr_compliance_service

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Check GDPR compliance for AI governance data processing'

    def add_arguments(self, parser):
        parser.add_argument(
            '--organization',
            type=int,
            help='Organization ID to check (required)',
            required=True
        )
        parser.add_argument(
            '--output-format',
            choices=['json', 'text', 'csv'],
            default='json',
            help='Output format for compliance results'
        )
        parser.add_argument(
            '--output-file',
            type=str,
            help='Output file path (if not specified, prints to stdout)'
        )
        parser.add_argument(
            '--generate-record',
            action='store_true',
            help='Generate GDPR Article 30 record of processing activities'
        )
        parser.add_argument(
            '--check-lawfulness',
            action='store_true',
            help='Check lawfulness of data processing'
        )

    def handle(self, *args, **options):
        organization_id = options['organization']
        output_format = options['output_format']
        output_file = options.get('output_file')
        generate_record = options['generate_record']
        check_lawfulness = options['check_lawfulness']

        try:
            # Get organization
            try:
                org = Organization.objects.get(id=organization_id)
            except Organization.DoesNotExist:
                raise CommandError(f'Organization with ID {organization_id} not found')

            self.stdout.write(
                self.style.SUCCESS(f'Starting GDPR compliance check for organization: {org.name}')
            )

            # Run GDPR compliance check within tenant context
            with tenant_context(org):
                compliance_results = {}

                # Check lawfulness of data processing
                if check_lawfulness:
                    self.stdout.write("Checking lawfulness of data processing...")
                    lawfulness_check = gdpr_compliance_service.check_data_processing_lawfulness(
                        purpose='AI governance and compliance testing',
                        data_types=['model_metadata', 'test_results', 'performance_metrics', 'compliance_data']
                    )
                    compliance_results['lawfulness_check'] = lawfulness_check

                # Generate record of processing activities
                if generate_record:
                    self.stdout.write("Generating record of processing activities...")
                    processing_record = gdpr_compliance_service.generate_data_processing_record(organization_id)
                    compliance_results['processing_record'] = processing_record

                # If no specific checks requested, run all checks
                if not check_lawfulness and not generate_record:
                    self.stdout.write("Running comprehensive GDPR compliance check...")
                    lawfulness_check = gdpr_compliance_service.check_data_processing_lawfulness(
                        purpose='AI governance and compliance testing',
                        data_types=['model_metadata', 'test_results', 'performance_metrics', 'compliance_data']
                    )
                    processing_record = gdpr_compliance_service.generate_data_processing_record(organization_id)
                    
                    compliance_results = {
                        'organization_id': organization_id,
                        'check_date': timezone.now().isoformat(),
                        'lawfulness_check': lawfulness_check,
                        'processing_record': processing_record,
                        'compliance_status': 'compliant',
                        'recommendations': [
                            'Ensure data minimization principles are followed',
                            'Implement appropriate technical and organizational measures',
                            'Maintain records of processing activities',
                            'Conduct regular privacy impact assessments',
                            'Implement data subject rights procedures',
                            'Establish data breach notification procedures'
                        ]
                    }

                # Format output
                if output_format == 'json':
                    output_content = self._format_json_output(compliance_results)
                elif output_format == 'text':
                    output_content = self._format_text_output(compliance_results)
                elif output_format == 'csv':
                    output_content = self._format_csv_output(compliance_results)

                # Write output
                if output_file:
                    with open(output_file, 'w') as f:
                        f.write(output_content)
                    self.stdout.write(
                        self.style.SUCCESS(f'GDPR compliance results written to: {output_file}')
                    )
                else:
                    self.stdout.write(output_content)

                # Print summary
                self._print_compliance_summary(compliance_results)

        except Exception as e:
            logger.error(f"GDPR compliance check failed: {e}")
            raise CommandError(f'GDPR compliance check failed: {e}')

    def _format_json_output(self, compliance_results):
        """Format compliance results as JSON."""
        return json.dumps(compliance_results, indent=2, default=str)

    def _format_text_output(self, compliance_results):
        """Format compliance results as human-readable text."""
        lines = []
        lines.append("=" * 80)
        lines.append("GDPR COMPLIANCE CHECK REPORT")
        lines.append("=" * 80)
        
        if 'organization_id' in compliance_results:
            lines.append(f"Organization ID: {compliance_results['organization_id']}")
        if 'check_date' in compliance_results:
            lines.append(f"Check Date: {compliance_results['check_date']}")
        if 'compliance_status' in compliance_results:
            lines.append(f"Compliance Status: {compliance_results['compliance_status'].upper()}")
        lines.append("")

        # Lawfulness check
        if 'lawfulness_check' in compliance_results:
            lawfulness = compliance_results['lawfulness_check']
            lines.append("LAWFULNESS OF DATA PROCESSING")
            lines.append("-" * 40)
            lines.append(f"Lawful Basis: {lawfulness['lawful_basis']}")
            lines.append(f"Description: {lawfulness['lawful_basis_description']}")
            lines.append(f"Purpose: {lawfulness['purpose']}")
            lines.append(f"Data Types: {', '.join(lawfulness['data_types'])}")
            lines.append(f"Compliance Status: {lawfulness['compliance_status']}")
            lines.append("")
            lines.append("Recommendations:")
            for i, rec in enumerate(lawfulness['recommendations'], 1):
                lines.append(f"  {i}. {rec}")
            lines.append("")

        # Processing record
        if 'processing_record' in compliance_results:
            record = compliance_results['processing_record']
            lines.append("RECORD OF PROCESSING ACTIVITIES (Article 30)")
            lines.append("-" * 40)
            lines.append(f"Organization ID: {record['organization_id']}")
            lines.append(f"Generated At: {record['generated_at']}")
            lines.append("")
            
            lines.append("Processing Activities:")
            for i, activity in enumerate(record['processing_activities'], 1):
                lines.append(f"  {i}. {activity['activity']}")
                lines.append(f"     Purpose: {activity['purpose']}")
                lines.append(f"     Data Categories: {', '.join(activity['data_categories'])}")
                lines.append(f"     Data Subjects: {', '.join(activity['data_subjects'])}")
                lines.append(f"     Lawful Basis: {activity['lawful_basis']}")
                lines.append(f"     Retention Period: {activity['retention_period']}")
                if 'data_volume' in activity:
                    lines.append(f"     Data Volume: {activity['data_volume']}")
                lines.append("")
            
            lines.append("Data Protection Measures:")
            for i, measure in enumerate(record['data_protection_measures'], 1):
                lines.append(f"  {i}. {measure}")
            lines.append("")
            
            lines.append("Data Subject Rights:")
            for i, right in enumerate(record['data_subject_rights'], 1):
                lines.append(f"  {i}. {right}")
            lines.append("")

        # General recommendations
        if 'recommendations' in compliance_results:
            lines.append("GENERAL RECOMMENDATIONS")
            lines.append("-" * 40)
            for i, rec in enumerate(compliance_results['recommendations'], 1):
                lines.append(f"{i}. {rec}")
            lines.append("")

        lines.append("=" * 80)
        return "\n".join(lines)

    def _format_csv_output(self, compliance_results):
        """Format compliance results as CSV."""
        import csv
        import io

        output = io.StringIO()
        writer = csv.writer(output)

        # Write header
        writer.writerow([
            'Organization ID', 'Check Date', 'Compliance Status',
            'Lawful Basis', 'Purpose', 'Data Types'
        ])

        # Write compliance data
        org_id = compliance_results.get('organization_id', '')
        check_date = compliance_results.get('check_date', '')
        compliance_status = compliance_results.get('compliance_status', '')
        
        if 'lawfulness_check' in compliance_results:
            lawfulness = compliance_results['lawfulness_check']
            writer.writerow([
                org_id,
                check_date,
                compliance_status,
                lawfulness.get('lawful_basis', ''),
                lawfulness.get('purpose', ''),
                ', '.join(lawfulness.get('data_types', []))
            ])
        else:
            writer.writerow([org_id, check_date, compliance_status, '', '', ''])

        return output.getvalue()

    def _print_compliance_summary(self, compliance_results):
        """Print compliance summary to console."""
        self.stdout.write("")
        self.stdout.write(self.style.SUCCESS("GDPR COMPLIANCE CHECK COMPLETED"))
        self.stdout.write("-" * 40)
        
        if 'compliance_status' in compliance_results:
            status = compliance_results['compliance_status']
            style = self.style.SUCCESS if status == 'compliant' else self.style.WARNING
            self.stdout.write(style(f"Compliance Status: {status.upper()}"))

        if 'lawfulness_check' in compliance_results:
            lawfulness = compliance_results['lawfulness_check']
            self.stdout.write(f"Lawful Basis: {lawfulness['lawful_basis']}")
            self.stdout.write(f"Purpose: {lawfulness['purpose']}")

        if 'processing_record' in compliance_results:
            record = compliance_results['processing_record']
            activities_count = len(record.get('processing_activities', []))
            self.stdout.write(f"Processing Activities: {activities_count}")

        if 'recommendations' in compliance_results:
            rec_count = len(compliance_results['recommendations'])
            self.stdout.write(f"Recommendations: {rec_count}")

        self.stdout.write("")
