from django.test import TestCase
from organizations.services import create_organization
from django.contrib.auth import get_user_model

class OrganizationServiceTest(TestCase):
    def test_create_organization_creates_all_entities(self):
        user = get_user_model().objects.create_user(username="a@b.com", email="a@b.com", password="pw")
        data = {
            'customer_code': 'ABCDEFGH',
            'customer_name': 'Test Org',
            'financial_year_end_date': '2025-12-31',
            'subscription_plan': 'premium',
            'start_date': '2025-01-01',
            'billing_cycle': 'yearly'
        }
        org = create_organization(data, created_by=user)
        self.assertTrue(org.settings.is_active)
        self.assertEqual(org.subscription.subscription_plan, 'premium')
