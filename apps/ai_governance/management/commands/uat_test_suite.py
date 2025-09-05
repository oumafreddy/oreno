# oreno/apps/ai_governance/management/commands/uat_test_suite.py

from django.core.management.base import BaseCommand, CommandError
from django_tenants.utils import tenant_context
from django.utils import timezone
from django.contrib.auth import get_user_model
import json
import logging
import os
import tempfile
import pandas as pd
import numpy as np
from datetime import timedelta

from organizations.models import Organization
from ai_governance.models import (
    ModelAsset, DatasetAsset, TestPlan, TestRun, TestResult, 
    Metric, EvidenceArtifact, Framework, Clause, ComplianceMapping
)
from ai_governance.tasks import execute_test_run
from ai_governance.security import pii_masking_service, gdpr_compliance_service

logger = logging.getLogger(__name__)
User = get_user_model()


class Command(BaseCommand):
    help = 'Run comprehensive UAT test suite for AI governance module'

    def add_arguments(self, parser):
        parser.add_argument(
            '--organization',
            type=int,
            help='Organization ID to run UAT tests (required)',
            required=True
        )
        parser.add_argument(
            '--test-category',
            choices=['all', 'models', 'datasets', 'test-plans', 'test-execution', 'security', 'compliance', 'reports'],
            default='all',
            help='Category of tests to run'
        )
        parser.add_argument(
            '--output-file',
            type=str,
            help='Output file path for UAT results (JSON format)'
        )
        parser.add_argument(
            '--create-sample-data',
            action='store_true',
            help='Create sample data for testing'
        )
        parser.add_argument(
            '--cleanup-after',
            action='store_true',
            help='Clean up test data after UAT completion'
        )

    def handle(self, *args, **options):
        organization_id = options['organization']
        test_category = options['test_category']
        output_file = options.get('output_file')
        create_sample_data = options['create_sample_data']
        cleanup_after = options['cleanup_after']

        try:
            # Get organization
            try:
                org = Organization.objects.get(id=organization_id)
            except Organization.DoesNotExist:
                raise CommandError(f'Organization with ID {organization_id} not found')

            self.stdout.write(
                self.style.SUCCESS(f'Starting UAT test suite for organization: {org.name}')
            )

            # Run UAT tests within tenant context
            with tenant_context(org):
                uat_results = {
                    'organization_id': organization_id,
                    'organization_name': org.name,
                    'test_date': timezone.now().isoformat(),
                    'test_category': test_category,
                    'tests_run': [],
                    'summary': {
                        'total_tests': 0,
                        'passed_tests': 0,
                        'failed_tests': 0,
                        'overall_status': 'pending'
                    }
                }

                # Create sample data if requested
                if create_sample_data:
                    self.stdout.write("Creating sample data for UAT...")
                    sample_data = self._create_sample_data(org)
                    uat_results['sample_data'] = sample_data

                # Run tests based on category
                if test_category in ['all', 'models']:
                    self._run_model_tests(uat_results)
                
                if test_category in ['all', 'datasets']:
                    self._run_dataset_tests(uat_results)
                
                if test_category in ['all', 'test-plans']:
                    self._run_test_plan_tests(uat_results)
                
                if test_category in ['all', 'test-execution']:
                    self._run_test_execution_tests(uat_results)
                
                if test_category in ['all', 'security']:
                    self._run_security_tests(uat_results)
                
                if test_category in ['all', 'compliance']:
                    self._run_compliance_tests(uat_results)
                
                if test_category in ['all', 'reports']:
                    self._run_report_tests(uat_results)

                # Calculate summary
                self._calculate_summary(uat_results)

                # Cleanup if requested
                if cleanup_after:
                    self.stdout.write("Cleaning up test data...")
                    self._cleanup_test_data(org)

                # Output results
                if output_file:
                    with open(output_file, 'w') as f:
                        json.dump(uat_results, f, indent=2, default=str)
                    self.stdout.write(
                        self.style.SUCCESS(f'UAT results written to: {output_file}')
                    )
                else:
                    self.stdout.write(json.dumps(uat_results, indent=2, default=str))

                # Print summary
                self._print_uat_summary(uat_results)

        except Exception as e:
            logger.error(f"UAT test suite failed: {e}")
            raise CommandError(f'UAT test suite failed: {e}')

    def _create_sample_data(self, org):
        """Create sample data for UAT testing."""
        sample_data = {
            'models_created': 0,
            'datasets_created': 0,
            'test_plans_created': 0,
            'test_runs_created': 0
        }

        # Create sample model assets
        model_assets = [
            {
                'name': 'UAT Credit Risk Model',
                'model_type': 'tabular',
                'uri': 's3://test-bucket/models/credit-risk-v1.0.pkl',
                'version': '1.0',
                'signature': {'input_features': ['age', 'income', 'credit_score'], 'output': 'risk_score'},
                'extra': {'algorithm': 'RandomForest', 'training_date': '2024-01-15'},
                'contains_pii': False,
                'data_classification': 'confidential'
            },
            {
                'name': 'UAT Image Classification Model',
                'model_type': 'image',
                'uri': 'mlflow://models/image-classifier/1',
                'version': '1.0',
                'signature': {'input_shape': [224, 224, 3], 'output_classes': 10},
                'extra': {'framework': 'TensorFlow', 'accuracy': 0.95},
                'contains_pii': False,
                'data_classification': 'internal'
            }
        ]

        for model_data in model_assets:
            model = ModelAsset.objects.create(
                organization=org,
                **model_data
            )
            sample_data['models_created'] += 1

        # Create sample dataset assets
        dataset_assets = [
            {
                'name': 'UAT Credit Dataset',
                'role': 'test',
                'path': 's3://test-bucket/datasets/credit-test.parquet',
                'format': 'parquet',
                'schema': {'age': 'int64', 'income': 'float64', 'credit_score': 'int64'},
                'sensitive_attributes': ['age'],
                'label': 'default_risk',
                'extra': {'size': 10000, 'features': 10},
                'contains_pii': True,
                'data_classification': 'confidential'
            },
            {
                'name': 'UAT Image Dataset',
                'role': 'test',
                'path': 's3://test-bucket/datasets/images-test.parquet',
                'format': 'parquet',
                'schema': {'image_path': 'string', 'label': 'int64'},
                'sensitive_attributes': [],
                'label': 'class',
                'extra': {'size': 5000, 'image_size': '224x224'},
                'contains_pii': False,
                'data_classification': 'internal'
            }
        ]

        for dataset_data in dataset_assets:
            dataset = DatasetAsset.objects.create(
                organization=org,
                **dataset_data
            )
            sample_data['datasets_created'] += 1

        # Create sample test plans
        test_plans = [
            {
                'name': 'UAT Tabular Model Test Plan',
                'model_type': 'tabular',
                'config': {
                    'tests': {
                        'demographic_parity': {
                            'enabled': True,
                            'parameters': {'sensitive_attribute': 'age'},
                            'thresholds': {'parity_score': 0.8}
                        },
                        'accuracy_test': {
                            'enabled': True,
                            'parameters': {'min_accuracy': 0.85},
                            'thresholds': {'accuracy': 0.85}
                        }
                    }
                },
                'alert_rules': {
                    'email_alerts': True,
                    'threshold_breach': True
                }
            },
            {
                'name': 'UAT Image Model Test Plan',
                'model_type': 'image',
                'config': {
                    'tests': {
                        'robustness_test': {
                            'enabled': True,
                            'parameters': {'noise_level': 0.1},
                            'thresholds': {'robustness_score': 0.9}
                        },
                        'explainability_test': {
                            'enabled': True,
                            'parameters': {'method': 'grad_cam'},
                            'thresholds': {'explainability_score': 0.8}
                        }
                    }
                },
                'alert_rules': {
                    'email_alerts': True,
                    'threshold_breach': True
                }
            }
        ]

        for plan_data in test_plans:
            plan = TestPlan.objects.create(
                organization=org,
                **plan_data
            )
            sample_data['test_plans_created'] += 1

        return sample_data

    def _run_model_tests(self, uat_results):
        """Run UAT tests for model assets."""
        self.stdout.write("Running model asset tests...")
        
        # Test 1: Model creation and validation
        test_result = self._run_test(
            'Model Creation and Validation',
            self._test_model_creation,
            'models'
        )
        uat_results['tests_run'].append(test_result)

        # Test 2: Model PII detection
        test_result = self._run_test(
            'Model PII Detection',
            self._test_model_pii_detection,
            'models'
        )
        uat_results['tests_run'].append(test_result)

        # Test 3: Model data classification
        test_result = self._run_test(
            'Model Data Classification',
            self._test_model_data_classification,
            'models'
        )
        uat_results['tests_run'].append(test_result)

    def _run_dataset_tests(self, uat_results):
        """Run UAT tests for dataset assets."""
        self.stdout.write("Running dataset asset tests...")
        
        # Test 1: Dataset creation and validation
        test_result = self._run_test(
            'Dataset Creation and Validation',
            self._test_dataset_creation,
            'datasets'
        )
        uat_results['tests_run'].append(test_result)

        # Test 2: Dataset PII detection
        test_result = self._run_test(
            'Dataset PII Detection',
            self._test_dataset_pii_detection,
            'datasets'
        )
        uat_results['tests_run'].append(test_result)

        # Test 3: Dataset schema validation
        test_result = self._run_test(
            'Dataset Schema Validation',
            self._test_dataset_schema_validation,
            'datasets'
        )
        uat_results['tests_run'].append(test_result)

    def _run_test_plan_tests(self, uat_results):
        """Run UAT tests for test plans."""
        self.stdout.write("Running test plan tests...")
        
        # Test 1: Test plan creation
        test_result = self._run_test(
            'Test Plan Creation',
            self._test_test_plan_creation,
            'test_plans'
        )
        uat_results['tests_run'].append(test_result)

        # Test 2: Test plan configuration validation
        test_result = self._run_test(
            'Test Plan Configuration Validation',
            self._test_test_plan_configuration,
            'test_plans'
        )
        uat_results['tests_run'].append(test_result)

    def _run_test_execution_tests(self, uat_results):
        """Run UAT tests for test execution."""
        self.stdout.write("Running test execution tests...")
        
        # Test 1: Test run creation
        test_result = self._run_test(
            'Test Run Creation',
            self._test_test_run_creation,
            'test_execution'
        )
        uat_results['tests_run'].append(test_result)

        # Test 2: Test execution (mock)
        test_result = self._run_test(
            'Test Execution (Mock)',
            self._test_test_execution_mock,
            'test_execution'
        )
        uat_results['tests_run'].append(test_result)

        # Test 3: Test result storage
        test_result = self._run_test(
            'Test Result Storage',
            self._test_test_result_storage,
            'test_execution'
        )
        uat_results['tests_run'].append(test_result)

    def _run_security_tests(self, uat_results):
        """Run UAT tests for security features."""
        self.stdout.write("Running security tests...")
        
        # Test 1: PII masking
        test_result = self._run_test(
            'PII Masking Service',
            self._test_pii_masking,
            'security'
        )
        uat_results['tests_run'].append(test_result)

        # Test 2: Data encryption
        test_result = self._run_test(
            'Data Encryption Service',
            self._test_data_encryption,
            'security'
        )
        uat_results['tests_run'].append(test_result)

        # Test 3: GDPR compliance
        test_result = self._run_test(
            'GDPR Compliance Check',
            self._test_gdpr_compliance,
            'security'
        )
        uat_results['tests_run'].append(test_result)

    def _run_compliance_tests(self, uat_results):
        """Run UAT tests for compliance features."""
        self.stdout.write("Running compliance tests...")
        
        # Test 1: Framework seeding
        test_result = self._run_test(
            'Compliance Framework Seeding',
            self._test_framework_seeding,
            'compliance'
        )
        uat_results['tests_run'].append(test_result)

        # Test 2: Compliance mapping
        test_result = self._run_test(
            'Compliance Mapping',
            self._test_compliance_mapping,
            'compliance'
        )
        uat_results['tests_run'].append(test_result)

    def _run_report_tests(self, uat_results):
        """Run UAT tests for reporting features."""
        self.stdout.write("Running report tests...")
        
        # Test 1: Report generation
        test_result = self._run_test(
            'Report Generation',
            self._test_report_generation,
            'reports'
        )
        uat_results['tests_run'].append(test_result)

    def _run_test(self, test_name, test_function, category):
        """Run a single test and return results."""
        try:
            result = test_function()
            return {
                'name': test_name,
                'category': category,
                'status': 'passed' if result else 'failed',
                'message': 'Test passed successfully' if result else 'Test failed',
                'timestamp': timezone.now().isoformat()
            }
        except Exception as e:
            return {
                'name': test_name,
                'category': category,
                'status': 'failed',
                'message': f'Test failed with error: {str(e)}',
                'timestamp': timezone.now().isoformat()
            }

    # Test implementations
    def _test_model_creation(self):
        """Test model asset creation and validation."""
        org = Organization.objects.get(id=self.organization_id)
        
        model = ModelAsset.objects.create(
            organization=org,
            name='UAT Test Model',
            model_type='tabular',
            uri='test://model.pkl',
            version='1.0',
            signature={'input': 'test'},
            extra={'test': True}
        )
        
        # Verify model was created
        assert model.id is not None
        assert model.organization == org
        assert model.name == 'UAT Test Model'
        
        return True

    def _test_model_pii_detection(self):
        """Test PII detection in model metadata."""
        org = Organization.objects.get(id=self.organization_id)
        
        # Create model with PII in metadata
        model = ModelAsset.objects.create(
            organization=org,
            name='UAT PII Test Model',
            model_type='tabular',
            uri='test://model.pkl',
            signature={'email': 'test@example.com', 'phone': '555-123-4567'},
            extra={'user_info': 'John Doe'}
        )
        
        # Check if PII was detected
        return model.contains_pii

    def _test_model_data_classification(self):
        """Test model data classification."""
        org = Organization.objects.get(id=self.organization_id)
        
        model = ModelAsset.objects.create(
            organization=org,
            name='UAT Classification Test Model',
            model_type='tabular',
            uri='test://model.pkl',
            data_classification='confidential'
        )
        
        return model.data_classification == 'confidential'

    def _test_dataset_creation(self):
        """Test dataset asset creation and validation."""
        org = Organization.objects.get(id=self.organization_id)
        
        dataset = DatasetAsset.objects.create(
            organization=org,
            name='UAT Test Dataset',
            role='test',
            path='test://dataset.parquet',
            format='parquet',
            schema={'feature1': 'float64', 'feature2': 'int64'},
            sensitive_attributes=['feature1']
        )
        
        # Verify dataset was created
        assert dataset.id is not None
        assert dataset.organization == org
        assert dataset.name == 'UAT Test Dataset'
        
        return True

    def _test_dataset_pii_detection(self):
        """Test PII detection in dataset metadata."""
        org = Organization.objects.get(id=self.organization_id)
        
        # Create dataset with PII in metadata
        dataset = DatasetAsset.objects.create(
            organization=org,
            name='UAT PII Test Dataset',
            role='test',
            path='test://dataset.parquet',
            schema={'email': 'string', 'phone': 'string'},
            sensitive_attributes=['email', 'phone'],
            extra={'description': 'Contains user emails like john@example.com'}
        )
        
        # Check if PII was detected
        return dataset.contains_pii

    def _test_dataset_schema_validation(self):
        """Test dataset schema validation."""
        org = Organization.objects.get(id=self.organization_id)
        
        dataset = DatasetAsset.objects.create(
            organization=org,
            name='UAT Schema Test Dataset',
            role='test',
            path='test://dataset.parquet',
            schema={'feature1': 'float64', 'feature2': 'int64', 'label': 'string'},
            label='label'
        )
        
        # Verify schema and label
        assert 'label' in dataset.schema
        assert dataset.label == 'label'
        
        return True

    def _test_test_plan_creation(self):
        """Test test plan creation."""
        org = Organization.objects.get(id=self.organization_id)
        
        plan = TestPlan.objects.create(
            organization=org,
            name='UAT Test Plan',
            model_type='tabular',
            config={
                'tests': {
                    'accuracy_test': {
                        'enabled': True,
                        'parameters': {'min_accuracy': 0.8},
                        'thresholds': {'accuracy': 0.8}
                    }
                }
            }
        )
        
        # Verify plan was created
        assert plan.id is not None
        assert plan.organization == org
        assert plan.name == 'UAT Test Plan'
        
        return True

    def _test_test_plan_configuration(self):
        """Test test plan configuration validation."""
        org = Organization.objects.get(id=self.organization_id)
        
        config = {
            'tests': {
                'fairness_test': {
                    'enabled': True,
                    'parameters': {'sensitive_attribute': 'age'},
                    'thresholds': {'parity_score': 0.8}
                },
                'robustness_test': {
                    'enabled': False,
                    'parameters': {'noise_level': 0.1},
                    'thresholds': {'robustness_score': 0.9}
                }
            }
        }
        
        plan = TestPlan.objects.create(
            organization=org,
            name='UAT Config Test Plan',
            model_type='tabular',
            config=config
        )
        
        # Verify configuration
        assert len(plan.config['tests']) == 2
        assert plan.config['tests']['fairness_test']['enabled'] is True
        assert plan.config['tests']['robustness_test']['enabled'] is False
        
        return True

    def _test_test_run_creation(self):
        """Test test run creation."""
        org = Organization.objects.get(id=self.organization_id)
        
        # Get or create required objects
        model = ModelAsset.objects.filter(organization=org).first()
        if not model:
            model = ModelAsset.objects.create(
                organization=org,
                name='UAT Test Model',
                model_type='tabular',
                uri='test://model.pkl'
            )
        
        dataset = DatasetAsset.objects.filter(organization=org).first()
        if not dataset:
            dataset = DatasetAsset.objects.create(
                organization=org,
                name='UAT Test Dataset',
                role='test',
                path='test://dataset.parquet'
            )
        
        plan = TestPlan.objects.filter(organization=org).first()
        if not plan:
            plan = TestPlan.objects.create(
                organization=org,
                name='UAT Test Plan',
                model_type='tabular',
                config={'tests': {}}
            )
        
        # Create test run
        test_run = TestRun.objects.create(
            organization=org,
            model_asset=model,
            dataset_asset=dataset,
            test_plan=plan,
            status='pending',
            parameters={'test_mode': True}
        )
        
        # Verify test run was created
        assert test_run.id is not None
        assert test_run.organization == org
        assert test_run.status == 'pending'
        
        return True

    def _test_test_execution_mock(self):
        """Test mock test execution."""
        org = Organization.objects.get(id=self.organization_id)
        
        # Get a test run
        test_run = TestRun.objects.filter(organization=org).first()
        if not test_run:
            return False
        
        # Mock test execution by updating status
        test_run.status = 'running'
        test_run.started_at = timezone.now()
        test_run.save()
        
        # Verify status update
        assert test_run.status == 'running'
        assert test_run.started_at is not None
        
        return True

    def _test_test_result_storage(self):
        """Test test result storage."""
        org = Organization.objects.get(id=self.organization_id)
        
        # Get a test run
        test_run = TestRun.objects.filter(organization=org).first()
        if not test_run:
            return False
        
        # Create test result
        test_result = TestResult.objects.create(
            organization=org,
            test_run=test_run,
            test_name='UAT Test',
            summary={'status': 'completed', 'score': 0.95},
            passed=True
        )
        
        # Create metric
        metric = Metric.objects.create(
            organization=org,
            test_result=test_result,
            name='accuracy',
            value=0.95,
            threshold=0.8,
            passed=True
        )
        
        # Verify results were created
        assert test_result.id is not None
        assert metric.id is not None
        assert test_result.passed is True
        assert metric.passed is True
        
        return True

    def _test_pii_masking(self):
        """Test PII masking service."""
        test_text = "Contact John Doe at john.doe@example.com or call (555) 123-4567"
        
        # Test PII detection
        detected_pii = pii_masking_service.detect_pii(test_text)
        assert 'email' in detected_pii
        assert 'phone' in detected_pii
        
        # Test PII masking
        masked_text, mask_counts = pii_masking_service.mask_pii(test_text)
        assert '@example.com' in masked_text  # Domain should remain
        assert '***' in masked_text  # Should contain masked content
        
        return True

    def _test_data_encryption(self):
        """Test data encryption service."""
        from ai_governance.security import encryption_service
        
        test_data = "sensitive test data"
        
        # Test encryption
        encrypted_data = encryption_service.encrypt_data(test_data)
        assert encrypted_data != test_data
        
        # Test decryption
        decrypted_data = encryption_service.decrypt_data(encrypted_data)
        assert decrypted_data == test_data
        
        return True

    def _test_gdpr_compliance(self):
        """Test GDPR compliance service."""
        org = Organization.objects.get(id=self.organization_id)
        
        # Test lawfulness check
        lawfulness = gdpr_compliance_service.check_data_processing_lawfulness(
            purpose='AI governance testing',
            data_types=['model_metadata', 'test_results']
        )
        
        assert lawfulness['compliance_status'] == 'compliant'
        assert 'lawful_basis' in lawfulness
        
        return True

    def _test_framework_seeding(self):
        """Test compliance framework seeding."""
        org = Organization.objects.get(id=self.organization_id)
        
        # Create a test framework
        framework = Framework.objects.create(
            organization=org,
            code='UAT_FRAMEWORK',
            title='UAT Test Framework',
            version='1.0',
            metadata={'description': 'Test framework for UAT'}
        )
        
        # Create a test clause
        clause = Clause.objects.create(
            organization=org,
            framework=framework,
            code='UAT_001',
            title='UAT Test Clause',
            description='Test clause for UAT',
            category='test'
        )
        
        # Verify framework and clause were created
        assert framework.id is not None
        assert clause.id is not None
        assert clause.framework == framework
        
        return True

    def _test_compliance_mapping(self):
        """Test compliance mapping."""
        org = Organization.objects.get(id=self.organization_id)
        
        # Get or create framework and clause
        framework = Framework.objects.filter(organization=org).first()
        if not framework:
            framework = Framework.objects.create(
                organization=org,
                code='UAT_FRAMEWORK',
                title='UAT Test Framework',
                version='1.0'
            )
        
        clause = Clause.objects.filter(organization=org).first()
        if not clause:
            clause = Clause.objects.create(
                organization=org,
                framework=framework,
                code='UAT_001',
                title='UAT Test Clause',
                description='Test clause',
                category='test'
            )
        
        # Get or create test result
        test_result = TestResult.objects.filter(organization=org).first()
        if not test_result:
            test_run = TestRun.objects.filter(organization=org).first()
            if not test_run:
                return False
            test_result = TestResult.objects.create(
                organization=org,
                test_run=test_run,
                test_name='UAT Test',
                summary={'status': 'completed'},
                passed=True
            )
        
        # Create compliance mapping
        mapping = ComplianceMapping.objects.create(
            organization=org,
            framework=framework,
            clause=clause,
            test_result=test_result,
            compliance_status='compliant',
            evidence='UAT test evidence'
        )
        
        # Verify mapping was created
        assert mapping.id is not None
        assert mapping.compliance_status == 'compliant'
        
        return True

    def _test_report_generation(self):
        """Test report generation."""
        org = Organization.objects.get(id=self.organization_id)
        
        # Test if we can generate a basic report
        # This would typically involve calling the report generation functions
        # For UAT, we'll just verify the report templates exist
        
        from django.template.loader import get_template
        
        try:
            # Check if report templates exist
            template = get_template('reports/ai_governance_dashboard.html')
            assert template is not None
            
            template = get_template('reports/ai_governance_test_run_details.html')
            assert template is not None
            
            template = get_template('reports/ai_governance_compliance_matrix.html')
            assert template is not None
            
            return True
        except Exception:
            return False

    def _calculate_summary(self, uat_results):
        """Calculate UAT test summary."""
        tests = uat_results['tests_run']
        total_tests = len(tests)
        passed_tests = sum(1 for test in tests if test['status'] == 'passed')
        failed_tests = total_tests - passed_tests
        
        uat_results['summary'] = {
            'total_tests': total_tests,
            'passed_tests': passed_tests,
            'failed_tests': failed_tests,
            'overall_status': 'passed' if failed_tests == 0 else 'failed',
            'success_rate': (passed_tests / total_tests * 100) if total_tests > 0 else 0
        }

    def _cleanup_test_data(self, org):
        """Clean up UAT test data."""
        # Delete test data created during UAT
        TestResult.objects.filter(organization=org, test_name__startswith='UAT').delete()
        TestRun.objects.filter(organization=org, parameters__test_mode=True).delete()
        TestPlan.objects.filter(organization=org, name__startswith='UAT').delete()
        DatasetAsset.objects.filter(organization=org, name__startswith='UAT').delete()
        ModelAsset.objects.filter(organization=org, name__startswith='UAT').delete()
        Framework.objects.filter(organization=org, code__startswith='UAT').delete()

    def _print_uat_summary(self, uat_results):
        """Print UAT summary to console."""
        self.stdout.write("")
        self.stdout.write(self.style.SUCCESS("UAT TEST SUITE COMPLETED"))
        self.stdout.write("-" * 40)
        
        summary = uat_results['summary']
        self.stdout.write(f"Total Tests: {summary['total_tests']}")
        self.stdout.write(f"Passed: {summary['passed_tests']}")
        self.stdout.write(f"Failed: {summary['failed_tests']}")
        self.stdout.write(f"Success Rate: {summary['success_rate']:.1f}%")
        
        status_style = self.style.SUCCESS if summary['overall_status'] == 'passed' else self.style.ERROR
        self.stdout.write(status_style(f"Overall Status: {summary['overall_status'].upper()}"))
        
        # Show failed tests
        failed_tests = [test for test in uat_results['tests_run'] if test['status'] == 'failed']
        if failed_tests:
            self.stdout.write("")
            self.stdout.write(self.style.ERROR("FAILED TESTS:"))
            for test in failed_tests:
                self.stdout.write(f"  - {test['name']}: {test['message']}")
        
        self.stdout.write("")
