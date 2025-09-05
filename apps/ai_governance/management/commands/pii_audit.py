# oreno/apps/ai_governance/management/commands/pii_audit.py

from django.core.management.base import BaseCommand, CommandError
from django_tenants.utils import tenant_context
from django.utils import timezone
import json
import logging

from organizations.models import Organization
from ai_governance.security import pii_masking_service
from ai_governance.models import TestRun, TestResult, EvidenceArtifact

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Audit AI governance data for PII and generate masking recommendations'

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
            '--data-type',
            choices=['test_runs', 'test_results', 'artifacts', 'all'],
            default='all',
            help='Type of data to audit for PII'
        )
        parser.add_argument(
            '--limit',
            type=int,
            default=100,
            help='Limit number of records to audit (default: 100)'
        )
        parser.add_argument(
            '--mask-pii',
            action='store_true',
            help='Generate masked versions of data containing PII'
        )

    def handle(self, *args, **options):
        organization_id = options['organization']
        output_format = options['output_format']
        output_file = options.get('output_file')
        data_type = options['data_type']
        limit = options['limit']
        mask_pii = options['mask_pii']

        try:
            # Get organization
            try:
                org = Organization.objects.get(id=organization_id)
            except Organization.DoesNotExist:
                raise CommandError(f'Organization with ID {organization_id} not found')

            self.stdout.write(
                self.style.SUCCESS(f'Starting PII audit for organization: {org.name}')
            )

            # Run PII audit within tenant context
            with tenant_context(org):
                audit_results = {
                    'organization_id': organization_id,
                    'audit_date': timezone.now().isoformat(),
                    'data_type': data_type,
                    'limit': limit,
                    'pii_findings': [],
                    'summary': {
                        'total_records_scanned': 0,
                        'records_with_pii': 0,
                        'pii_types_found': {},
                        'total_pii_instances': 0
                    }
                }

                # Define data types to process
                if data_type == 'all':
                    data_types = ['test_runs', 'test_results', 'artifacts']
                else:
                    data_types = [data_type]

                # Process each data type
                for dt in data_types:
                    self.stdout.write(f"Auditing {dt} for PII...")
                    findings = self._audit_data_type(dt, limit, mask_pii)
                    audit_results['pii_findings'].extend(findings)

                # Calculate summary
                self._calculate_audit_summary(audit_results)

                # Format output
                if output_format == 'json':
                    output_content = self._format_json_output(audit_results)
                elif output_format == 'text':
                    output_content = self._format_text_output(audit_results)
                elif output_format == 'csv':
                    output_content = self._format_csv_output(audit_results)

                # Write output
                if output_file:
                    with open(output_file, 'w') as f:
                        f.write(output_content)
                    self.stdout.write(
                        self.style.SUCCESS(f'PII audit results written to: {output_file}')
                    )
                else:
                    self.stdout.write(output_content)

                # Print summary
                self._print_audit_summary(audit_results)

        except Exception as e:
            logger.error(f"PII audit failed: {e}")
            raise CommandError(f'PII audit failed: {e}')

    def _audit_data_type(self, data_type, limit, mask_pii):
        """Audit specific data type for PII."""
        findings = []
        
        if data_type == 'test_runs':
            queryset = TestRun.objects.all()[:limit]
            for record in queryset:
                finding = self._audit_record(record, 'test_run', mask_pii)
                if finding:
                    findings.append(finding)
        
        elif data_type == 'test_results':
            queryset = TestResult.objects.all()[:limit]
            for record in queryset:
                finding = self._audit_record(record, 'test_result', mask_pii)
                if finding:
                    findings.append(finding)
        
        elif data_type == 'artifacts':
            queryset = EvidenceArtifact.objects.all()[:limit]
            for record in queryset:
                finding = self._audit_record(record, 'artifact', mask_pii)
                if finding:
                    findings.append(finding)
        
        return findings

    def _audit_record(self, record, record_type, mask_pii):
        """Audit individual record for PII."""
        finding = {
            'record_type': record_type,
            'record_id': record.id,
            'pii_detected': {},
            'masked_data': {},
            'pii_count': 0
        }
        
        # Check text fields for PII
        text_fields = []
        if hasattr(record, 'summary') and record.summary:
            text_fields.append(('summary', record.summary))
        if hasattr(record, 'description') and record.description:
            text_fields.append(('description', record.description))
        if hasattr(record, 'metadata') and record.metadata:
            text_fields.append(('metadata', str(record.metadata)))
        if hasattr(record, 'parameters') and record.parameters:
            text_fields.append(('parameters', str(record.parameters)))
        
        for field_name, field_value in text_fields:
            if isinstance(field_value, str):
                detected_pii = pii_masking_service.detect_pii(field_value)
                if detected_pii:
                    finding['pii_detected'][field_name] = detected_pii
                    finding['pii_count'] += sum(len(matches) for matches in detected_pii.values())
                    
                    if mask_pii:
                        masked_value, mask_counts = pii_masking_service.mask_pii(field_value)
                        finding['masked_data'][field_name] = {
                            'original': field_value,
                            'masked': masked_value,
                            'mask_counts': mask_counts
                        }
        
        # Only return finding if PII was detected
        if finding['pii_count'] > 0:
            return finding
        return None

    def _calculate_audit_summary(self, audit_results):
        """Calculate audit summary statistics."""
        summary = audit_results['summary']
        findings = audit_results['pii_findings']
        
        summary['total_records_scanned'] = len(findings)
        summary['records_with_pii'] = len(findings)
        
        # Count PII types
        pii_types = {}
        total_pii_instances = 0
        
        for finding in findings:
            for field_name, detected_pii in finding['pii_detected'].items():
                for pii_type, matches in detected_pii.items():
                    if pii_type not in pii_types:
                        pii_types[pii_type] = 0
                    pii_types[pii_type] += len(matches)
                    total_pii_instances += len(matches)
        
        summary['pii_types_found'] = pii_types
        summary['total_pii_instances'] = total_pii_instances

    def _format_json_output(self, audit_results):
        """Format audit results as JSON."""
        return json.dumps(audit_results, indent=2, default=str)

    def _format_text_output(self, audit_results):
        """Format audit results as human-readable text."""
        lines = []
        lines.append("=" * 80)
        lines.append("PII AUDIT REPORT")
        lines.append("=" * 80)
        lines.append(f"Organization ID: {audit_results['organization_id']}")
        lines.append(f"Audit Date: {audit_results['audit_date']}")
        lines.append(f"Data Type: {audit_results['data_type']}")
        lines.append(f"Limit: {audit_results['limit']}")
        lines.append("")

        # Summary
        summary = audit_results['summary']
        lines.append("SUMMARY")
        lines.append("-" * 40)
        lines.append(f"Total Records Scanned: {summary['total_records_scanned']}")
        lines.append(f"Records with PII: {summary['records_with_pii']}")
        lines.append(f"Total PII Instances: {summary['total_pii_instances']}")
        lines.append("")

        # PII types found
        if summary['pii_types_found']:
            lines.append("PII TYPES FOUND")
            lines.append("-" * 40)
            for pii_type, count in summary['pii_types_found'].items():
                lines.append(f"{pii_type.upper()}: {count}")
            lines.append("")

        # Detailed findings
        if audit_results['pii_findings']:
            lines.append("DETAILED FINDINGS")
            lines.append("-" * 40)
            for i, finding in enumerate(audit_results['pii_findings'], 1):
                lines.append(f"{i}. {finding['record_type'].upper()} ID: {finding['record_id']}")
                lines.append(f"   PII Count: {finding['pii_count']}")
                
                for field_name, detected_pii in finding['pii_detected'].items():
                    lines.append(f"   Field: {field_name}")
                    for pii_type, matches in detected_pii.items():
                        lines.append(f"     {pii_type}: {len(matches)} instances")
                
                if finding['masked_data']:
                    lines.append("   Masked Data Available: Yes")
                
                lines.append("")

        lines.append("=" * 80)
        return "\n".join(lines)

    def _format_csv_output(self, audit_results):
        """Format audit results as CSV."""
        import csv
        import io

        output = io.StringIO()
        writer = csv.writer(output)

        # Write header
        writer.writerow([
            'Organization ID', 'Audit Date', 'Record Type', 'Record ID',
            'Field Name', 'PII Type', 'PII Count', 'PII Instances'
        ])

        # Write findings
        for finding in audit_results['pii_findings']:
            for field_name, detected_pii in finding['pii_detected'].items():
                for pii_type, matches in detected_pii.items():
                    writer.writerow([
                        audit_results['organization_id'],
                        audit_results['audit_date'],
                        finding['record_type'],
                        finding['record_id'],
                        field_name,
                        pii_type,
                        len(matches),
                        ', '.join(matches)
                    ])

        return output.getvalue()

    def _print_audit_summary(self, audit_results):
        """Print audit summary to console."""
        self.stdout.write("")
        self.stdout.write(self.style.SUCCESS("PII AUDIT COMPLETED"))
        self.stdout.write("-" * 40)
        
        summary = audit_results['summary']
        self.stdout.write(f"Total Records Scanned: {summary['total_records_scanned']}")
        self.stdout.write(f"Records with PII: {summary['records_with_pii']}")
        self.stdout.write(f"Total PII Instances: {summary['total_pii_instances']}")
        
        if summary['pii_types_found']:
            self.stdout.write("PII Types Found:")
            for pii_type, count in summary['pii_types_found'].items():
                style = self.style.ERROR if count > 0 else self.style.SUCCESS
                self.stdout.write(style(f"  {pii_type.upper()}: {count}"))
        
        self.stdout.write("")
