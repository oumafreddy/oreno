"""
Management command to seed AI governance compliance frameworks.
"""

from django.core.management.base import BaseCommand
from django.db import transaction
from django_tenants.utils import tenant_context
from organizations.models import Organization

from ai_governance.models import Framework, Clause, ComplianceMapping


class Command(BaseCommand):
    help = 'Seed AI governance compliance frameworks (EU AI Act, OECD, NIST)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--organization',
            type=str,
            help='Organization ID to seed frameworks for (default: all organizations)'
        )
        parser.add_argument(
            '--framework',
            type=str,
            choices=['eu_ai_act', 'oecd', 'nist', 'all'],
            default='all',
            help='Framework to seed (default: all)'
        )

    def handle(self, *args, **options):
        org_id = options.get('organization')
        framework_choice = options.get('framework')

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
                self.style.WARNING('No organizations found to seed frameworks')
            )
            return

        # Seed frameworks for each organization
        for org in organizations:
            self.stdout.write(f'Seeding frameworks for organization: {org.name}')
            
            with tenant_context(org):
                with transaction.atomic():
                    if framework_choice in ['eu_ai_act', 'all']:
                        self._seed_eu_ai_act(org)
                    
                    if framework_choice in ['oecd', 'all']:
                        self._seed_oecd_principles(org)
                    
                    if framework_choice in ['nist', 'all']:
                        self._seed_nist_ai_rmf(org)

        self.stdout.write(
            self.style.SUCCESS('Successfully seeded compliance frameworks')
        )

    def _seed_eu_ai_act(self, org):
        """Seed EU AI Act framework."""
        self.stdout.write('  Seeding EU AI Act framework...')
        
        # Create framework
        framework, created = Framework.objects.get_or_create(
            organization=org,
            code='EU_AI_ACT',
            defaults={
                'title': 'EU Artificial Intelligence Act',
                'version': '2024',
                'metadata': {
                    'description': 'Regulation on artificial intelligence by the European Union',
                    'jurisdiction': 'European Union',
                    'effective_date': '2024-08-02',
                    'risk_categories': ['minimal', 'limited', 'high', 'unacceptable']
                }
            }
        )
        
        if created:
            self.stdout.write(f'    Created framework: {framework.title}')
        
        # Define EU AI Act clauses
        eu_clauses = [
            {
                'clause_code': 'ART_5',
                'text': 'Prohibited AI practices that contravene Union values',
                'metadata': {'article': 5, 'category': 'prohibited_practices'}
            },
            {
                'clause_code': 'ART_6',
                'text': 'High-risk AI systems subject to conformity assessment',
                'metadata': {'article': 6, 'category': 'high_risk_systems'}
            },
            {
                'clause_code': 'ART_8',
                'text': 'Requirements for high-risk AI systems',
                'metadata': {'article': 8, 'category': 'requirements'}
            },
            {
                'clause_code': 'ART_10',
                'text': 'Data governance and management practices',
                'metadata': {'article': 10, 'category': 'data_governance'}
            },
            {
                'clause_code': 'ART_13',
                'text': 'Transparency and provision of information to users',
                'metadata': {'article': 13, 'category': 'transparency'}
            },
            {
                'clause_code': 'ART_14',
                'text': 'Human oversight requirements',
                'metadata': {'article': 14, 'category': 'human_oversight'}
            },
            {
                'clause_code': 'ART_15',
                'text': 'Accuracy, robustness and cybersecurity requirements',
                'metadata': {'article': 15, 'category': 'accuracy_robustness'}
            }
        ]
        
        self._create_clauses(framework, eu_clauses)
        
        # Create compliance mappings
        eu_mappings = [
            {
                'test_name': 'demographic_parity',
                'clause_code': 'ART_5',
                'rationale': 'Demographic parity testing ensures AI systems do not discriminate based on protected characteristics, addressing prohibited practices under Article 5.'
            },
            {
                'test_name': 'equal_opportunity',
                'clause_code': 'ART_5',
                'rationale': 'Equal opportunity testing verifies that AI systems provide equal opportunities across different groups, preventing discriminatory practices.'
            },
            {
                'test_name': 'shap_feature_importance',
                'clause_code': 'ART_13',
                'rationale': 'SHAP explanations provide transparency about model decisions, supporting Article 13 transparency requirements.'
            },
            {
                'test_name': 'adversarial_noise',
                'clause_code': 'ART_15',
                'rationale': 'Adversarial robustness testing ensures model accuracy and robustness under attack conditions, meeting Article 15 requirements.'
            },
            {
                'test_name': 'membership_inference',
                'clause_code': 'ART_10',
                'rationale': 'Membership inference testing validates data governance practices and prevents data leakage, supporting Article 10 requirements.'
            }
        ]
        
        self._create_compliance_mappings(framework, eu_mappings)

    def _seed_oecd_principles(self, org):
        """Seed OECD AI Principles framework."""
        self.stdout.write('  Seeding OECD AI Principles framework...')
        
        # Create framework
        framework, created = Framework.objects.get_or_create(
            organization=org,
            code='OECD_AI_PRINCIPLES',
            defaults={
                'title': 'OECD Principles on Artificial Intelligence',
                'version': '2019',
                'metadata': {
                    'description': 'Principles for responsible stewardship of trustworthy AI',
                    'jurisdiction': 'International',
                    'effective_date': '2019-05-22',
                    'principles': ['inclusive_growth', 'human_centered', 'transparency', 'robustness', 'accountability']
                }
            }
        )
        
        if created:
            self.stdout.write(f'    Created framework: {framework.title}')
        
        # Define OECD principles
        oecd_clauses = [
            {
                'clause_code': 'PRINCIPLE_1',
                'text': 'AI should benefit people and the planet by driving inclusive growth, sustainable development and well-being',
                'metadata': {'principle': 1, 'category': 'inclusive_growth'}
            },
            {
                'clause_code': 'PRINCIPLE_2',
                'text': 'AI systems should be designed in a way that respects the rule of law, human rights, democratic values and diversity',
                'metadata': {'principle': 2, 'category': 'human_centered'}
            },
            {
                'clause_code': 'PRINCIPLE_3',
                'text': 'There should be transparency and responsible disclosure around AI systems to ensure that people understand AI-based outcomes',
                'metadata': {'principle': 3, 'category': 'transparency'}
            },
            {
                'clause_code': 'PRINCIPLE_4',
                'text': 'AI systems should function in a robust, secure and safe way throughout their life cycles',
                'metadata': {'principle': 4, 'category': 'robustness'}
            },
            {
                'clause_code': 'PRINCIPLE_5',
                'text': 'Organizations and individuals developing, deploying or operating AI systems should be held accountable for their proper functioning',
                'metadata': {'principle': 5, 'category': 'accountability'}
            }
        ]
        
        self._create_clauses(framework, oecd_clauses)
        
        # Create compliance mappings
        oecd_mappings = [
            {
                'test_name': 'demographic_parity',
                'clause_code': 'PRINCIPLE_2',
                'rationale': 'Demographic parity testing ensures AI systems respect human rights and diversity, supporting Principle 2.'
            },
            {
                'test_name': 'shap_feature_importance',
                'clause_code': 'PRINCIPLE_3',
                'rationale': 'SHAP explanations provide transparency about AI decision-making processes, supporting Principle 3.'
            },
            {
                'test_name': 'lime_explanations',
                'clause_code': 'PRINCIPLE_3',
                'rationale': 'LIME explanations help users understand AI-based outcomes, supporting transparency requirements.'
            },
            {
                'test_name': 'adversarial_noise',
                'clause_code': 'PRINCIPLE_4',
                'rationale': 'Robustness testing ensures AI systems function securely and safely, supporting Principle 4.'
            },
            {
                'test_name': 'stability_test',
                'clause_code': 'PRINCIPLE_4',
                'rationale': 'Stability testing validates robust functioning throughout the AI system lifecycle.'
            },
            {
                'test_name': 'data_leakage',
                'clause_code': 'PRINCIPLE_5',
                'rationale': 'Data leakage testing supports accountability by ensuring proper data governance practices.'
            }
        ]
        
        self._create_compliance_mappings(framework, oecd_mappings)

    def _seed_nist_ai_rmf(self, org):
        """Seed NIST AI Risk Management Framework."""
        self.stdout.write('  Seeding NIST AI RMF framework...')
        
        # Create framework
        framework, created = Framework.objects.get_or_create(
            organization=org,
            code='NIST_AI_RMF',
            defaults={
                'title': 'NIST AI Risk Management Framework',
                'version': '1.0',
                'metadata': {
                    'description': 'Framework for managing risks to individuals, organizations, and society associated with AI',
                    'jurisdiction': 'United States',
                    'effective_date': '2023-01-26',
                    'functions': ['govern', 'map', 'measure', 'manage']
                }
            }
        )
        
        if created:
            self.stdout.write(f'    Created framework: {framework.title}')
        
        # Define NIST AI RMF functions and outcomes
        nist_clauses = [
            {
                'clause_code': 'GOVERN_1',
                'text': 'Establish AI risk management governance and culture',
                'metadata': {'function': 'govern', 'outcome': 1, 'category': 'governance'}
            },
            {
                'clause_code': 'GOVERN_2',
                'text': 'Define AI risk management roles and responsibilities',
                'metadata': {'function': 'govern', 'outcome': 2, 'category': 'governance'}
            },
            {
                'clause_code': 'MAP_1',
                'text': 'Identify and document AI system context and use',
                'metadata': {'function': 'map', 'outcome': 1, 'category': 'mapping'}
            },
            {
                'clause_code': 'MAP_2',
                'text': 'Identify and assess AI system risks',
                'metadata': {'function': 'map', 'outcome': 2, 'category': 'mapping'}
            },
            {
                'clause_code': 'MEASURE_1',
                'text': 'Establish AI system performance and risk metrics',
                'metadata': {'function': 'measure', 'outcome': 1, 'category': 'measurement'}
            },
            {
                'clause_code': 'MEASURE_2',
                'text': 'Monitor AI system performance and risk metrics',
                'metadata': {'function': 'measure', 'outcome': 2, 'category': 'measurement'}
            },
            {
                'clause_code': 'MANAGE_1',
                'text': 'Implement AI system risk controls',
                'metadata': {'function': 'manage', 'outcome': 1, 'category': 'management'}
            },
            {
                'clause_code': 'MANAGE_2',
                'text': 'Monitor and review AI system risk controls',
                'metadata': {'function': 'manage', 'outcome': 2, 'category': 'management'}
            }
        ]
        
        self._create_clauses(framework, nist_clauses)
        
        # Create compliance mappings
        nist_mappings = [
            {
                'test_name': 'demographic_parity',
                'clause_code': 'MAP_2',
                'rationale': 'Demographic parity testing helps identify and assess bias-related risks in AI systems.'
            },
            {
                'test_name': 'equal_opportunity',
                'clause_code': 'MAP_2',
                'rationale': 'Equal opportunity testing identifies discrimination risks that need to be managed.'
            },
            {
                'test_name': 'shap_feature_importance',
                'clause_code': 'MEASURE_1',
                'rationale': 'SHAP explanations provide measurable insights into model behavior for risk assessment.'
            },
            {
                'test_name': 'permutation_importance',
                'clause_code': 'MEASURE_1',
                'rationale': 'Permutation importance establishes measurable metrics for feature impact on model performance.'
            },
            {
                'test_name': 'adversarial_noise',
                'clause_code': 'MEASURE_2',
                'rationale': 'Adversarial robustness testing monitors system performance under attack conditions.'
            },
            {
                'test_name': 'stability_test',
                'clause_code': 'MEASURE_2',
                'rationale': 'Stability testing monitors consistent performance across different conditions.'
            },
            {
                'test_name': 'membership_inference',
                'clause_code': 'MANAGE_1',
                'rationale': 'Membership inference testing helps implement privacy controls to manage data leakage risks.'
            },
            {
                'test_name': 'data_leakage',
                'clause_code': 'MANAGE_2',
                'rationale': 'Data leakage testing monitors and reviews data governance controls.'
            }
        ]
        
        self._create_compliance_mappings(framework, nist_mappings)

    def _create_clauses(self, framework, clauses_data):
        """Create clauses for a framework."""
        for clause_data in clauses_data:
            clause, created = Clause.objects.get_or_create(
                framework=framework,
                clause_code=clause_data['clause_code'],
                defaults={
                    'text': clause_data['text'],
                    'metadata': clause_data['metadata'],
                    'organization': framework.organization
                }
            )
            
            if created:
                self.stdout.write(f'    Created clause: {clause.clause_code}')

    def _create_compliance_mappings(self, framework, mappings_data):
        """Create compliance mappings for a framework."""
        for mapping_data in mappings_data:
            try:
                clause = Clause.objects.get(
                    framework=framework,
                    clause_code=mapping_data['clause_code']
                )
                
                mapping, created = ComplianceMapping.objects.get_or_create(
                    organization=framework.organization,
                    test_name=mapping_data['test_name'],
                    clause=clause,
                    defaults={
                        'rationale': mapping_data['rationale'],
                        'evidence_rule': {
                            'pass_threshold': 0.7,
                            'metric_requirements': ['score', 'passed']
                        }
                    }
                )
                
                if created:
                    self.stdout.write(f'    Created mapping: {mapping.test_name} -> {clause.clause_code}')
                    
            except Clause.DoesNotExist:
                self.stdout.write(
                    self.style.WARNING(
                        f'    Clause {mapping_data["clause_code"]} not found for mapping {mapping_data["test_name"]}'
                    )
                )