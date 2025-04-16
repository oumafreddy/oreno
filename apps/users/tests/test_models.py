# apps/users/tests/test_models.py

from django.test import TestCase
from django.contrib.auth import get_user_model
from apps.organizations.models.organization import Organization
from datetime import date

CustomUser = get_user_model()

class CustomUserModelTest(TestCase):
    def setUp(self):
        self.organization = Organization.objects.create(
            customer_code="ORG002",
            customer_name="Demo Organization",
            financial_year_end_date=date(2024, 12, 31),
            customer_industry="Education"
        )
        self.user = CustomUser.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpassword123",
            organization=self.organization
        )

    def test_user_str(self):
        self.assertEqual(str(self.user), self.user.email)

    def test_user_organization_relationship(self):
        # Ensure user has an organization assigned
        self.assertIsNotNone(self.user.organization)
        self.assertEqual(self.user.organization, self.organization)
