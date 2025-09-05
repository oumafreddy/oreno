# oreno/apps/ai_governance/management/commands/generate_uat_data.py

from django.core.management.base import BaseCommand, CommandError
from django_tenants.utils import tenant_context
from django.utils import timezone
from django.contrib.auth import get_user_model
import json
import logging
import random
import string
from datetime import timedelta

from organizations.models import Organization
from ai_governance.models import (
    ModelAsset, DatasetAsset, TestPlan, TestRun, TestResult, 
    Metric, EvidenceArtifact, Framework, Clause, ComplianceMapping,
    ConnectorConfig, WebhookSubscription
)

logger = logging.getLogger(__name__)
User = get_user_model()


class Command(BaseCommand):
    help = 'Generate comprehensive UAT test data for AI governance module'

    def add_arguments(self, parser):
        parser.add_argument(
            '--organization',
            type=int,
            help='Organization ID to generate UAT data (required)',
            required=True
        )
        parser.add_argument(
            '--data-size',
            choices=['small', 'medium', 'large'],
            default='medium',
            help='Size of test data to generate'
        )
        parser.add_argument(
            '--include-users',
            action='store_true',
            help='Generate test users'
        )
        parser.add_argument(
            '--include-webhooks',
            action='store_true',
            help='Generate webhook subscriptions'
        )
        parser.add_argument(
            '--include-connectors',
            action='store_true',
            help='Generate connector configurations'
        )

    def handle(self, *args, **options):
        organization_id = options['organization']
        data_size = options['data_size']
        include_users = options['include_users']
        include_webhooks = options['include_webhooks']
        include_connectors = options['include_connectors']

        try:
            # Get organization
            try:
                org = Organization.objects.get(id=organization_id)
            except Organization.DoesNotExist:
                raise CommandError(f'Organization with ID {organization_id} not found')

            self.stdout.write(
                self.style.SUCCESS(f'Generating UAT test data for organization: {org.name}')
            )

            # Generate data within tenant context
            with tenant_context(org):
                generation_results = {
                    'organization_id': organization_id,
                    'organization_name': org.name,
                    'generation_date': timezone.now().isoformat(),
                    'data_size': data_size,
                    'data_generated': {}
                }

                # Determine data quantities based on size
                quantities = self._get_data_quantities(data_size)

                # Generate test data
                if include_users:
                    self.stdout.write("Generating test users...")
                    users_data = self._generate_test_users(org, quantities['users'])
                    generation_results['data_generated']['users'] = users_data

                self.stdout.write("Generating model assets...")
                models_data = self._generate_model_assets(org, quantities['models'])
                generation_results['data_generated']['models'] = models_data

                self.stdout.write("Generating dataset assets...")
                datasets_data = self._generate_dataset_assets(org, quantities['datasets'])
                generation_results['data_generated']['datasets'] = datasets_data

                self.stdout.write("Generating test plans...")
                plans_data = self._generate_test_plans(org, quantities['test_plans'])
                generation_results['data_generated']['test_plans'] = plans_data

                self.stdout.write("Generating test runs...")
                runs_data = self._generate_test_runs(org, quantities['test_runs'])
                generation_results['data_generated']['test_runs'] = runs_data

                self.stdout.write("Generating test results...")
                results_data = self._generate_test_results(org, quantities['test_results'])
                generation_results['data_generated']['test_results'] = results_data

                self.stdout.write("Generating metrics...")
                metrics_data = self._generate_metrics(org, quantities['metrics'])
                generation_results['data_generated']['metrics'] = metrics_data

                self.stdout.write("Generating evidence artifacts...")
                artifacts_data = self._generate_evidence_artifacts(org, quantities['artifacts'])
                generation_results['data_generated']['artifacts'] = artifacts_data

                self.stdout.write("Generating compliance frameworks...")
                frameworks_data = self._generate_frameworks(org, quantities['frameworks'])
                generation_results['data_generated']['frameworks'] = frameworks_data

                if include_connectors:
                    self.stdout.write("Generating connector configurations...")
                    connectors_data = self._generate_connectors(org, quantities['connectors'])
                    generation_results['data_generated']['connectors'] = connectors_data

                if include_webhooks:
                    self.stdout.write("Generating webhook subscriptions...")
                    webhooks_data = self._generate_webhooks(org, quantities['webhooks'])
                    generation_results['data_generated']['webhooks'] = webhooks_data

                # Print summary
                self._print_generation_summary(generation_results)

        except Exception as e:
            logger.error(f"UAT data generation failed: {e}")
            raise CommandError(f'UAT data generation failed: {e}')

    def _get_data_quantities(self, data_size):
        """Get data quantities based on size."""
        quantities = {
            'small': {
                'users': 3,
                'models': 5,
                'datasets': 5,
                'test_plans': 3,
                'test_runs': 10,
                'test_results': 20,
                'metrics': 50,
                'artifacts': 15,
                'frameworks': 3,
                'connectors': 2,
                'webhooks': 2
            },
            'medium': {
                'users': 10,
                'models': 20,
                'datasets': 20,
                'test_plans': 10,
                'test_runs': 50,
                'test_results': 100,
                'metrics': 250,
                'artifacts': 75,
                'frameworks': 5,
                'connectors': 5,
                'webhooks': 5
            },
            'large': {
                'users': 25,
                'models': 50,
                'datasets': 50,
                'test_plans': 25,
                'test_runs': 150,
                'test_results': 300,
                'metrics': 750,
                'artifacts': 200,
                'frameworks': 10,
                'connectors': 10,
                'webhooks': 10
            }
        }
        return quantities[data_size]

    def _generate_test_users(self, org, count):
        """Generate test users."""
        users_created = 0
        roles = ['admin', 'manager', 'staff']
        
        for i in range(count):
            role = random.choice(roles)
            user, created = User.objects.get_or_create(
                email=f'uat_user_{i+1}@example.com',
                defaults={
                    'username': f'uat_user_{i+1}',
                    'first_name': f'UAT',
                    'last_name': f'User{i+1}',
                    'organization': org,
                    'role': role,
                    'is_active': True
                }
            )
            
            if created:
                user.set_password('uat_test_password')
                user.save()
                users_created += 1
        
        return {'created': users_created, 'total': count}

    def _generate_model_assets(self, org, count):
        """Generate model assets."""
        models_created = 0
        model_types = ['tabular', 'image', 'generative']
        algorithms = ['RandomForest', 'XGBoost', 'Neural Network', 'SVM', 'Logistic Regression']
        classifications = ['public', 'internal', 'confidential', 'restricted']
        
        for i in range(count):
            model_type = random.choice(model_types)
            algorithm = random.choice(algorithms)
            classification = random.choice(classifications)
            
            model = ModelAsset.objects.create(
                organization=org,
                name=f'UAT Model {i+1} - {model_type.title()}',
                model_type=model_type,
                uri=f's3://uat-bucket/models/{model_type}-model-{i+1}.pkl',
                version=f'1.{i}',
                signature={
                    'input_features': [f'feature_{j}' for j in range(random.randint(5, 20))],
                    'output': 'prediction',
                    'input_shape': [224, 224, 3] if model_type == 'image' else None
                },
                extra={
                    'algorithm': algorithm,
                    'accuracy': round(random.uniform(0.7, 0.99), 3),
                    'training_date': (timezone.now() - timedelta(days=random.randint(1, 365))).isoformat(),
                    'dataset_size': random.randint(1000, 100000)
                },
                contains_pii=random.choice([True, False]),
                data_classification=classification,
                encryption_key_id=f'key_{i+1}' if classification in ['confidential', 'restricted'] else None
            )
            models_created += 1
        
        return {'created': models_created, 'total': count}

    def _generate_dataset_assets(self, org, count):
        """Generate dataset assets."""
        datasets_created = 0
        roles = ['train', 'validation', 'test', 'other']
        formats = ['parquet', 'csv', 'json']
        classifications = ['public', 'internal', 'confidential', 'restricted']
        
        for i in range(count):
            role = random.choice(roles)
            format_type = random.choice(formats)
            classification = random.choice(classifications)
            
            # Generate schema
            feature_count = random.randint(5, 20)
            schema = {}
            sensitive_attrs = []
            
            for j in range(feature_count):
                feature_name = f'feature_{j}'
                feature_type = random.choice(['float64', 'int64', 'string', 'boolean'])
                schema[feature_name] = feature_type
                
                # Mark some features as sensitive
                if random.random() < 0.3:  # 30% chance
                    sensitive_attrs.append(feature_name)
            
            dataset = DatasetAsset.objects.create(
                organization=org,
                name=f'UAT Dataset {i+1} - {role.title()}',
                role=role,
                path=f's3://uat-bucket/datasets/{role}-dataset-{i+1}.{format_type}',
                format=format_type,
                schema=schema,
                sensitive_attributes=sensitive_attrs,
                label='target' if random.random() < 0.8 else None,
                extra={
                    'size': random.randint(1000, 100000),
                    'features': feature_count,
                    'created_date': (timezone.now() - timedelta(days=random.randint(1, 365))).isoformat()
                },
                contains_pii=len(sensitive_attrs) > 0,
                data_classification=classification,
                encryption_key_id=f'key_{i+1}' if classification in ['confidential', 'restricted'] else None,
                retention_date=timezone.now() + timedelta(days=random.randint(30, 365))
            )
            datasets_created += 1
        
        return {'created': datasets_created, 'total': count}

    def _generate_test_plans(self, org, count):
        """Generate test plans."""
        plans_created = 0
        model_types = ['tabular', 'image', 'generative']
        test_types = ['accuracy', 'fairness', 'robustness', 'explainability', 'privacy']
        
        for i in range(count):
            model_type = random.choice(model_types)
            selected_tests = random.sample(test_types, random.randint(2, 4))
            
            config = {'tests': {}}
            for test_type in selected_tests:
                config['tests'][f'{test_type}_test'] = {
                    'enabled': random.choice([True, False]),
                    'parameters': self._get_test_parameters(test_type),
                    'thresholds': self._get_test_thresholds(test_type),
                    'timeout': random.randint(30, 300)
                }
            
            plan = TestPlan.objects.create(
                organization=org,
                name=f'UAT Test Plan {i+1} - {model_type.title()}',
                model_type=model_type,
                config=config,
                alert_rules={
                    'email_alerts': random.choice([True, False]),
                    'threshold_breach': True,
                    'test_failure': True,
                    'webhook_notifications': random.choice([True, False])
                }
            )
            plans_created += 1
        
        return {'created': plans_created, 'total': count}

    def _get_test_parameters(self, test_type):
        """Get test parameters based on test type."""
        parameters = {
            'accuracy': {'min_accuracy': round(random.uniform(0.7, 0.95), 2)},
            'fairness': {'sensitive_attribute': random.choice(['age', 'gender', 'race'])},
            'robustness': {'noise_level': round(random.uniform(0.01, 0.1), 3)},
            'explainability': {'method': random.choice(['shap', 'lime', 'grad_cam'])},
            'privacy': {'privacy_budget': round(random.uniform(0.1, 1.0), 2)}
        }
        return parameters.get(test_type, {})

    def _get_test_thresholds(self, test_type):
        """Get test thresholds based on test type."""
        thresholds = {
            'accuracy': {'accuracy': round(random.uniform(0.8, 0.95), 2)},
            'fairness': {'parity_score': round(random.uniform(0.7, 0.9), 2)},
            'robustness': {'robustness_score': round(random.uniform(0.8, 0.95), 2)},
            'explainability': {'explainability_score': round(random.uniform(0.7, 0.9), 2)},
            'privacy': {'privacy_score': round(random.uniform(0.8, 0.95), 2)}
        }
        return thresholds.get(test_type, {})

    def _generate_test_runs(self, org, count):
        """Generate test runs."""
        runs_created = 0
        models = list(ModelAsset.objects.filter(organization=org))
        datasets = list(DatasetAsset.objects.filter(organization=org))
        plans = list(TestPlan.objects.filter(organization=org))
        statuses = ['pending', 'running', 'completed', 'failed', 'cancelled']
        
        for i in range(count):
            model = random.choice(models) if models else None
            dataset = random.choice(datasets) if datasets else None
            plan = random.choice(plans) if plans else None
            status = random.choice(statuses)
            
            # Set timestamps based on status
            started_at = None
            completed_at = None
            
            if status in ['running', 'completed', 'failed']:
                started_at = timezone.now() - timedelta(hours=random.randint(1, 24))
            
            if status in ['completed', 'failed']:
                completed_at = started_at + timedelta(minutes=random.randint(5, 120))
            
            test_run = TestRun.objects.create(
                organization=org,
                model_asset=model,
                dataset_asset=dataset,
                test_plan=plan,
                status=status,
                parameters={
                    'test_mode': True,
                    'random_seed': random.randint(1, 1000),
                    'timeout': random.randint(60, 600)
                },
                started_at=started_at,
                completed_at=completed_at,
                error_message=f'Test error message {i+1}' if status == 'failed' else '',
                worker_info={
                    'task_id': f'task_{i+1}',
                    'worker': f'worker_{random.randint(1, 5)}'
                } if status in ['running', 'completed', 'failed'] else {},
                contains_pii=model.contains_pii if model else False,
                data_classification=model.data_classification if model else 'internal',
                retention_date=timezone.now() + timedelta(days=random.randint(30, 365))
            )
            runs_created += 1
        
        return {'created': runs_created, 'total': count}

    def _generate_test_results(self, org, count):
        """Generate test results."""
        results_created = 0
        test_runs = list(TestRun.objects.filter(organization=org))
        test_names = ['accuracy_test', 'fairness_test', 'robustness_test', 'explainability_test', 'privacy_test']
        
        for i in range(count):
            test_run = random.choice(test_runs) if test_runs else None
            test_name = random.choice(test_names)
            passed = random.choice([True, False])
            
            test_result = TestResult.objects.create(
                organization=org,
                test_run=test_run,
                test_name=test_name,
                summary={
                    'status': 'completed',
                    'score': round(random.uniform(0.5, 1.0), 3),
                    'execution_time': round(random.uniform(1.0, 60.0), 2),
                    'metadata': {
                        'test_version': '1.0',
                        'random_seed': random.randint(1, 1000)
                    }
                },
                passed=passed,
                contains_pii=test_run.contains_pii if test_run else False,
                data_classification=test_run.data_classification if test_run else 'internal'
            )
            results_created += 1
        
        return {'created': results_created, 'total': count}

    def _generate_metrics(self, org, count):
        """Generate metrics."""
        metrics_created = 0
        test_results = list(TestResult.objects.filter(organization=org))
        metric_names = ['accuracy', 'precision', 'recall', 'f1_score', 'auc', 'parity_score', 'robustness_score']
        
        for i in range(count):
            test_result = random.choice(test_results) if test_results else None
            metric_name = random.choice(metric_names)
            value = round(random.uniform(0.0, 1.0), 3)
            threshold = round(random.uniform(0.5, 0.9), 3)
            passed = value >= threshold
            
            metric = Metric.objects.create(
                organization=org,
                test_result=test_result,
                name=metric_name,
                value=value,
                threshold=threshold,
                passed=passed,
                slice_key=random.choice(['age_group', 'gender', 'region']) if random.random() < 0.3 else None,
                slice_value=random.choice(['18-25', '26-35', 'male', 'female', 'north', 'south']) if random.random() < 0.3 else None,
                extra={
                    'confidence_interval': [round(value - 0.05, 3), round(value + 0.05, 3)],
                    'sample_size': random.randint(100, 10000)
                }
            )
            metrics_created += 1
        
        return {'created': metrics_created, 'total': count}

    def _generate_evidence_artifacts(self, org, count):
        """Generate evidence artifacts."""
        artifacts_created = 0
        test_runs = list(TestRun.objects.filter(organization=org))
        artifact_types = ['pdf', 'image', 'json', 'csv', 'log', 'other']
        
        for i in range(count):
            test_run = random.choice(test_runs) if test_runs else None
            artifact_type = random.choice(artifact_types)
            
            artifact = EvidenceArtifact.objects.create(
                organization=org,
                test_run=test_run,
                artifact_type=artifact_type,
                file_path=f's3://uat-bucket/artifacts/{artifact_type}-artifact-{i+1}.{artifact_type}',
                file_info={
                    'size_bytes': random.randint(1024, 10485760),  # 1KB to 10MB
                    'created_at': timezone.now().isoformat(),
                    'checksum': ''.join(random.choices(string.hexdigits, k=32))
                },
                contains_pii=test_run.contains_pii if test_run else False,
                data_classification=test_run.data_classification if test_run else 'internal',
                retention_date=timezone.now() + timedelta(days=random.randint(30, 365))
            )
            artifacts_created += 1
        
        return {'created': artifacts_created, 'total': count}

    def _generate_frameworks(self, org, count):
        """Generate compliance frameworks."""
        frameworks_created = 0
        framework_data = [
            {'code': 'EU_AI_ACT', 'title': 'EU AI Act', 'version': '1.0'},
            {'code': 'OECD_AI', 'title': 'OECD AI Principles', 'version': '1.0'},
            {'code': 'NIST_AI_RMF', 'title': 'NIST AI RMF', 'version': '1.0'},
            {'code': 'ISO_23053', 'title': 'ISO/IEC 23053', 'version': '1.0'},
            {'code': 'IEEE_2859', 'title': 'IEEE 2859', 'version': '1.0'}
        ]
        
        for i in range(min(count, len(framework_data))):
            framework_info = framework_data[i]
            
            framework = Framework.objects.create(
                organization=org,
                code=framework_info['code'],
                title=framework_info['title'],
                version=framework_info['version'],
                metadata={
                    'description': f'Test framework for {framework_info["title"]}',
                    'jurisdiction': random.choice(['EU', 'US', 'Global']),
                    'effective_date': '2024-01-01'
                }
            )
            
            # Create clauses for this framework
            clause_count = random.randint(5, 15)
            for j in range(clause_count):
                Clause.objects.create(
                    organization=org,
                    framework=framework,
                    code=f'{framework_info["code"]}_{j+1:03d}',
                    title=f'Clause {j+1} - {framework_info["title"]}',
                    description=f'Test clause {j+1} for {framework_info["title"]}',
                    category=random.choice(['technical', 'organizational', 'legal']),
                    severity=random.choice(['low', 'medium', 'high', 'critical'])
                )
            
            frameworks_created += 1
        
        return {'created': frameworks_created, 'total': count}

    def _generate_connectors(self, org, count):
        """Generate connector configurations."""
        connectors_created = 0
        connector_types = ['mlflow', 's3', 'azure_blob', 'gcs', 'huggingface']
        
        for i in range(count):
            connector_type = random.choice(connector_types)
            
            connector = ConnectorConfig.objects.create(
                organization=org,
                name=f'UAT {connector_type.title()} Connector {i+1}',
                connector_type=connector_type,
                config={
                    'endpoint': f'https://{connector_type}.example.com',
                    'region': random.choice(['us-east-1', 'us-west-2', 'eu-west-1']),
                    'bucket': f'uat-{connector_type}-bucket-{i+1}'
                },
                is_active=random.choice([True, False]),
                last_sync=timezone.now() - timedelta(hours=random.randint(1, 24)) if random.random() < 0.8 else None
            )
            connectors_created += 1
        
        return {'created': connectors_created, 'total': count}

    def _generate_webhooks(self, org, count):
        """Generate webhook subscriptions."""
        webhooks_created = 0
        events = ['test_run.started', 'test_run.completed', 'test_run.failed', 'threshold.breached']
        
        for i in range(count):
            event = random.choice(events)
            
            webhook = WebhookSubscription.objects.create(
                organization=org,
                name=f'UAT Webhook {i+1}',
                url=f'https://webhook.example.com/uat-{i+1}',
                events=[event],
                is_active=random.choice([True, False]),
                secret_key=f'secret_key_{i+1}',
                retry_count=random.randint(0, 3),
                timeout=random.randint(5, 30)
            )
            webhooks_created += 1
        
        return {'created': webhooks_created, 'total': count}

    def _print_generation_summary(self, generation_results):
        """Print data generation summary to console."""
        self.stdout.write("")
        self.stdout.write(self.style.SUCCESS("UAT DATA GENERATION COMPLETED"))
        self.stdout.write("-" * 50)
        
        data_generated = generation_results['data_generated']
        total_created = 0
        
        for data_type, info in data_generated.items():
            created = info['created']
            total = info['total']
            total_created += created
            self.stdout.write(f"{data_type.replace('_', ' ').title()}: {created}/{total}")
        
        self.stdout.write(f"Total Records Created: {total_created}")
        self.stdout.write("")
