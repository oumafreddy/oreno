"""
Management command to seed sample AI governance data for testing.
"""

from django.core.management.base import BaseCommand
from django.db import transaction
from django_tenants.utils import tenant_context
from organizations.models import Organization

from ai_governance.models import ModelAsset, DatasetAsset, TestPlan


class Command(BaseCommand):
    help = 'Seed sample AI governance data (models, datasets, test plans)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--organization',
            type=str,
            help='Organization ID to seed data for (default: all organizations)'
        )

    def handle(self, *args, **options):
        org_id = options.get('organization')

        # Get organizations to seed
        if org_id:
            try:
                organizations = [Organization.objects.get(id=org_id)]
            except Organization.DoesNotExist:
                self.stdout.write(
                    self.style.ERROR(f'Organization with ID {org_id} not found')
                )
                return
        else:
            organizations = Organization.objects.all()

        if not organizations:
            self.stdout.write(
                self.style.WARNING('No organizations found to seed data')
            )
            return

        # Seed data for each organization
        for org in organizations:
            self.stdout.write(f'Seeding sample data for organization: {org.name}')
            
            with tenant_context(org):
                with transaction.atomic():
                    self._seed_sample_models(org)
                    self._seed_sample_datasets(org)
                    self._seed_sample_test_plans(org)

        self.stdout.write(
            self.style.SUCCESS('Successfully seeded sample AI governance data')
        )

    def _seed_sample_models(self, org):
        """Seed sample model assets."""
        self.stdout.write('  Seeding sample models...')
        
        sample_models = [
            {
                'name': 'Credit Risk Classifier',
                'model_type': 'tabular',
                'uri': 'mlflow://models/credit-risk/1',
                'version': '1.0.0',
                'signature': {
                    'inputs': ['age', 'income', 'credit_score', 'debt_ratio'],
                    'outputs': ['risk_score']
                },
                'extra': {
                    'description': 'Binary classifier for credit risk assessment',
                    'training_date': '2024-01-15',
                    'accuracy': 0.87
                }
            },
            {
                'name': 'Image Classification Model',
                'model_type': 'image',
                'uri': 's3://models/image-classifier/v2',
                'version': '2.1.0',
                'signature': {
                    'inputs': ['image_tensor'],
                    'outputs': ['class_probabilities']
                },
                'extra': {
                    'description': 'CNN for medical image classification',
                    'training_date': '2024-02-20',
                    'accuracy': 0.94
                }
            },
            {
                'name': 'Text Generation Model',
                'model_type': 'generative',
                'uri': 'huggingface://gpt-2-medium',
                'version': 'latest',
                'signature': {
                    'inputs': ['text_prompt'],
                    'outputs': ['generated_text']
                },
                'extra': {
                    'description': 'GPT-2 based text generation model',
                    'training_date': '2024-03-10',
                    'parameters': '355M'
                }
            }
        ]
        
        for model_data in sample_models:
            model, created = ModelAsset.objects.get_or_create(
                organization=org,
                name=model_data['name'],
                defaults=model_data
            )
            
            if created:
                self.stdout.write(f'    Created model: {model.name}')

    def _seed_sample_datasets(self, org):
        """Seed sample dataset assets."""
        self.stdout.write('  Seeding sample datasets...')
        
        sample_datasets = [
            {
                'name': 'Credit Risk Training Data',
                'role': 'train',
                'path': 's3://datasets/credit-risk/train.csv',
                'format': 'csv',
                'schema': {
                    'columns': ['age', 'income', 'credit_score', 'debt_ratio', 'default'],
                    'types': ['int', 'float', 'int', 'float', 'bool']
                },
                'sensitive_attributes': ['age'],
                'label': 'default',
                'extra': {
                    'description': 'Historical credit data for training',
                    'size': '100K records',
                    'date_range': '2020-2023'
                }
            },
            {
                'name': 'Credit Risk Test Data',
                'role': 'test',
                'path': 's3://datasets/credit-risk/test.csv',
                'format': 'csv',
                'schema': {
                    'columns': ['age', 'income', 'credit_score', 'debt_ratio', 'default'],
                    'types': ['int', 'float', 'int', 'float', 'bool']
                },
                'sensitive_attributes': ['age'],
                'label': 'default',
                'extra': {
                    'description': 'Holdout test data for evaluation',
                    'size': '20K records',
                    'date_range': '2024'
                }
            },
            {
                'name': 'Medical Images Dataset',
                'role': 'train',
                'path': 's3://datasets/medical-images/train/',
                'format': 'parquet',
                'schema': {
                    'columns': ['image_path', 'diagnosis', 'patient_id'],
                    'types': ['string', 'string', 'string']
                },
                'sensitive_attributes': ['patient_id'],
                'label': 'diagnosis',
                'extra': {
                    'description': 'Medical imaging dataset for classification',
                    'size': '50K images',
                    'classes': ['normal', 'abnormal']
                }
            }
        ]
        
        for dataset_data in sample_datasets:
            dataset, created = DatasetAsset.objects.get_or_create(
                organization=org,
                name=dataset_data['name'],
                defaults=dataset_data
            )
            
            if created:
                self.stdout.write(f'    Created dataset: {dataset.name}')

    def _seed_sample_test_plans(self, org):
        """Seed sample test plans."""
        self.stdout.write('  Seeding sample test plans...')
        
        sample_test_plans = [
            {
                'name': 'Comprehensive Tabular Testing',
                'model_type': 'tabular',
                'config': {
                    'tests': {
                        'demographic_parity': {
                            'enabled': True,
                            'parameters': {
                                'sensitive_attribute': 'age',
                                'privileged_group': 'young'
                            },
                            'thresholds': {
                                'demographic_parity': 0.1
                            }
                        },
                        'shap_feature_importance': {
                            'enabled': True,
                            'parameters': {
                                'max_features': 10
                            },
                            'thresholds': {
                                'min_importance': 0.05
                            }
                        },
                        'adversarial_noise': {
                            'enabled': True,
                            'parameters': {
                                'noise_levels': [0.01, 0.05, 0.1]
                            },
                            'thresholds': {
                                'min_robustness': 0.8
                            }
                        }
                    }
                },
                'alert_rules': {
                    'email_alerts': True,
                    'threshold_breach': True,
                    'test_failure': True
                }
            },
            {
                'name': 'Image Model Validation',
                'model_type': 'image',
                'config': {
                    'tests': {
                        'shap_feature_importance': {
                            'enabled': True,
                            'parameters': {
                                'max_features': 5
                            }
                        },
                        'adversarial_noise': {
                            'enabled': True,
                            'parameters': {
                                'noise_levels': [0.01, 0.02, 0.05]
                            }
                        },
                        'stability_test': {
                            'enabled': True,
                            'parameters': {
                                'num_runs': 3
                            }
                        }
                    }
                },
                'alert_rules': {
                    'email_alerts': True,
                    'threshold_breach': True
                }
            }
        ]
        
        for plan_data in sample_test_plans:
            plan, created = TestPlan.objects.get_or_create(
                organization=org,
                name=plan_data['name'],
                defaults=plan_data
            )
            
            if created:
                self.stdout.write(f'    Created test plan: {plan.name}')
