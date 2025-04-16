# apps/users/tests/test_auth.py

from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from apps.organizations.models.organization import Organization
from datetime import date

CustomUser = get_user_model()

class AuthTest(TestCase):
    def setUp(self):
        self.organization = Organization.objects.create(
            customer_code="ORG003",
            customer_name="Auth Org",
            financial_year_end_date=date(2024, 12, 31),
            customer_industry="Finance"
        )
        self.user = CustomUser.objects.create_user(
            username="authuser",
            email="auth@example.com",
            password="securepassword",
            organization=self.organization
        )
        self.login_url = reverse('login')  # Update to your login route

    def test_login(self):
        # Use the test client to login
        response = self.client.post(self.login_url, {
            'username': self.user.email,
            'password': 'securepassword'
        })
        # Check if redirection happens after login
        self.assertEqual(response.status_code, 302)
        # Subsequent access to a protected page should succeed
        response = self.client.get(reverse('home'))  # Assuming 'home' is a protected page
        self.assertEqual(response.status_code, 200)
