"""
Tests for Enhanced Schema Index
"""
from django.test import TestCase
from services.agent.schema_index import EnhancedSchemaIndex, get_schema_index, rebuild_schema_index


class SchemaIndexTestCase(TestCase):
    """Test cases for schema index"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.schema_index = EnhancedSchemaIndex().build()
    
    def test_schema_index_builds(self):
        """Test that schema index builds successfully"""
        self.assertIsNotNone(self.schema_index)
        self.assertGreater(len(self.schema_index.models), 0)
    
    def test_audit_workplan_indexed(self):
        """Test that AuditWorkplan is indexed"""
        schema = self.schema_index.get_model_schema('audit.AuditWorkplan')
        self.assertIsNotNone(schema)
        self.assertEqual(schema['model'], 'AuditWorkplan')
        self.assertEqual(schema['app'], 'audit')
    
    def test_field_extraction(self):
        """Test that fields are extracted correctly"""
        schema = self.schema_index.get_model_schema('audit.AuditWorkplan')
        self.assertIn('fields', schema)
        self.assertIn('code', schema['fields'])
        self.assertIn('name', schema['fields'])
        self.assertIn('fiscal_year', schema['fields'])
    
    def test_field_metadata(self):
        """Test that field metadata is comprehensive"""
        field_info = self.schema_index.get_field_info('audit.AuditWorkplan', 'code')
        self.assertIsNotNone(field_info)
        self.assertIn('type', field_info)
        self.assertIn('required', field_info)
        self.assertIn('max_length', field_info)
    
    def test_relationships_extracted(self):
        """Test that relationships are extracted"""
        schema = self.schema_index.get_model_schema('audit.AuditWorkplan')
        self.assertIn('relationships', schema)
    
    def test_workflow_detection(self):
        """Test that workflow states are detected"""
        schema = self.schema_index.get_model_schema('audit.AuditWorkplan')
        self.assertIn('workflow', schema)
        # AuditWorkplan should have a state machine
        if schema['workflow']['has_state_machine']:
            self.assertIn('states', schema['workflow'])
            self.assertIn('state_field', schema['workflow'])
    
    def test_serializer_indexing(self):
        """Test that serializers are indexed"""
        serializer_info = self.schema_index.get_serializer_for_model('audit.AuditWorkplan')
        # May or may not have serializer, but if it does, should have fields
        if serializer_info:
            self.assertIn('fields', serializer_info)
    
    def test_form_indexing(self):
        """Test that forms are indexed"""
        form_info = self.schema_index.get_form_for_model('audit.AuditWorkplan')
        # May or may not have form, but if it does, should have fields
        if form_info:
            self.assertIn('fields', form_info)
    
    def test_list_models(self):
        """Test listing models"""
        models = self.schema_index.list_models()
        self.assertGreater(len(models), 0)
        self.assertIn('audit.AuditWorkplan', models)
    
    def test_list_models_by_app(self):
        """Test listing models filtered by app"""
        audit_models = self.schema_index.list_models('audit')
        self.assertGreater(len(audit_models), 0)
        self.assertTrue(all(m.startswith('audit.') for m in audit_models))
    
    def test_get_schema_index_singleton(self):
        """Test that get_schema_index returns singleton"""
        index1 = get_schema_index()
        index2 = get_schema_index()
        self.assertIs(index1, index2)
    
    def test_rebuild_schema_index(self):
        """Test rebuilding schema index"""
        new_index = rebuild_schema_index()
        self.assertIsNotNone(new_index)
        self.assertGreater(len(new_index.models), 0)

