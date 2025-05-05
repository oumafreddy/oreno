# apps/organizations/tests/test_models.py

from django.test import TestCase
#from organizations.models.organization import Organization
from ..models.organization import Organization
from django.urls import reverse
from datetime import date

class OrganizationModelTest(TestCase):
    def setUp(self):
        self.organization = Organization.objects.create(
            customer_code="ORG001",
            customer_name="Test Organization",
            financial_year_end_date=date(2024, 12, 31),
            customer_industry="Technology"
        )

    def test_organization_str(self):
        expected_str = "Test Organization (Technology)"
        self.assertEqual(str(self.organization), expected_str)

    def test_get_absolute_url(self):
        # Ensure the URL returns correctly
        self.assertEqual(self.organization.get_absolute_url(), reverse('organization_detail', args=[self.organization.id]))

    def test_get_employees_empty(self):
        # Initially no users are associated
        self.assertEqual(self.organization.get_employees().count(), 0)
