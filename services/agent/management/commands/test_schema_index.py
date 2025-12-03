"""
Management command to test and display schema index information
"""
from django.core.management.base import BaseCommand
from services.agent.schema_index import get_schema_index
import json


class Command(BaseCommand):
    help = 'Test and display schema index information'

    def add_arguments(self, parser):
        parser.add_argument(
            '--model',
            type=str,
            help='Show detailed info for a specific model (e.g., audit.AuditWorkplan)',
        )
        parser.add_argument(
            '--list',
            action='store_true',
            help='List all indexed models',
        )
        parser.add_argument(
            '--app',
            type=str,
            help='List models for a specific app',
        )
        parser.add_argument(
            '--field',
            type=str,
            help='Show info for a specific field (requires --model)',
        )
        parser.add_argument(
            '--stats',
            action='store_true',
            help='Show statistics about the schema index',
        )

    def handle(self, *args, **options):
        schema_index = get_schema_index()
        
        if options['stats']:
            self.show_stats(schema_index)
        elif options['list']:
            self.list_models(schema_index, options.get('app'))
        elif options['model']:
            if options['field']:
                self.show_field(schema_index, options['model'], options['field'])
            else:
                self.show_model(schema_index, options['model'])
        else:
            # Default: show stats
            self.show_stats(schema_index)

    def show_stats(self, schema_index):
        """Show statistics about the schema index"""
        self.stdout.write(self.style.SUCCESS('\n=== Schema Index Statistics ===\n'))
        self.stdout.write(f"Total Models Indexed: {len(schema_index.models)}")
        self.stdout.write(f"Total Serializers Indexed: {len(schema_index.serializers)}")
        self.stdout.write(f"Total Forms Indexed: {len(schema_index.forms)}\n")
        
        # Count by app
        apps = {}
        for model_path in schema_index.models.keys():
            app = model_path.split('.')[0]
            apps[app] = apps.get(app, 0) + 1
        
        self.stdout.write("Models by App:")
        for app, count in sorted(apps.items()):
            self.stdout.write(f"  {app}: {count} models")
        
        # Count models with workflows
        workflow_count = sum(
            1 for s in schema_index.models.values()
            if s.get('workflow', {}).get('has_state_machine', False)
        )
        self.stdout.write(f"\nModels with State Machines: {workflow_count}")

    def list_models(self, schema_index, app_name=None):
        """List all models"""
        models = schema_index.list_models(app_name=app_name)
        self.stdout.write(self.style.SUCCESS(f'\n=== Models{" (" + app_name + ")" if app_name else ""} ===\n'))
        for model_path in sorted(models):
            schema = schema_index.get_model_schema(model_path)
            verbose_name = schema.get('meta', {}).get('verbose_name', model_path)
            self.stdout.write(f"  {model_path} - {verbose_name}")

    def show_model(self, schema_index, model_path):
        """Show detailed info for a model"""
        schema = schema_index.get_model_schema(model_path)
        if not schema:
            self.stdout.write(self.style.ERROR(f"Model '{model_path}' not found"))
            return
        
        self.stdout.write(self.style.SUCCESS(f'\n=== Model: {model_path} ===\n'))
        self.stdout.write(f"App: {schema['app']}")
        self.stdout.write(f"DB Table: {schema.get('db_table', 'N/A')}")
        self.stdout.write(f"Verbose Name: {schema.get('meta', {}).get('verbose_name', 'N/A')}\n")
        
        # Fields
        self.stdout.write(f"Fields ({len(schema['fields'])}):")
        for field_name, field_info in sorted(schema['fields'].items()):
            field_type = field_info.get('type', 'Unknown')
            required = "✓" if field_info.get('required', False) else " "
            self.stdout.write(f"  {required} {field_name} ({field_type})")
        
        # Relationships
        if schema.get('relationships'):
            self.stdout.write(f"\nRelationships ({len(schema['relationships'])}):")
            for rel_name, rel_info in schema['relationships'].items():
                self.stdout.write(f"  {rel_name} -> {rel_info.get('related_model', 'N/A')}")
        
        # Workflow
        workflow = schema.get('workflow', {})
        if workflow.get('has_state_machine'):
            self.stdout.write(f"\nState Machine:")
            self.stdout.write(f"  State Field: {workflow.get('state_field', 'N/A')}")
            self.stdout.write(f"  States: {', '.join(workflow.get('states', []))}")
        
        # Serializer
        if 'serializer' in schema:
            self.stdout.write(f"\nSerializer: {schema['serializer']}")
        
        # Form
        if 'form' in schema:
            self.stdout.write(f"Form: {schema['form']}")

    def show_field(self, schema_index, model_path, field_name):
        """Show detailed info for a field"""
        field_info = schema_index.get_field_info(model_path, field_name)
        if not field_info:
            self.stdout.write(self.style.ERROR(f"Field '{field_name}' not found in model '{model_path}'"))
            return
        
        self.stdout.write(self.style.SUCCESS(f'\n=== Field: {model_path}.{field_name} ===\n'))
        self.stdout.write(json.dumps(field_info, indent=2, default=str))

