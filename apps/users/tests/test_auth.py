# apps/users/tests/test_auth.py

from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
from apps.organizations.models import Organization
from datetime import date

User = get_user_model()

class AuthenticationTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        # Create organization with required fields
        self.org = Organization.objects.create(
            customer_code='TEST01',
            customer_name='Test Organization',
            customer_industry='Tech',
            financial_year_end_date=date.today(),
        )
        # Create admin user
        self.admin_user = User.objects.create_user(
            email='admin@test.com',
            username='admin',
            password='testpass',
            organization=self.org,
            role='admin'
        )
        # Create staff user
        self.staff_user = User.objects.create_user(
            email='staff@test.com',
            username='staff',
            password='testpass',
            organization=self.org,
            role='staff'
        )

    def test_user_registration(self):
        url = reverse('users:user-login')
        data = {
            'email': 'new@test.com',
            'username': 'newuser',
            'password': 'TestPass123!',
            'organization': self.org.id
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(User.objects.filter(email='new@test.com').exists())

    def test_user_login(self):
        url = reverse('user-login')
        data = {
            'email': 'admin@test.com',
            'password': 'testpass'
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)

    def test_cross_organization_access(self):
        # Create a second organization with all required fields
        org2 = Organization.objects.create(
            customer_code='TEST02',
            customer_name='Test Org 2',
            customer_industry='Finance',
            financial_year_end_date=date.today(),
        )
        # Admin from org1 tries to access org2 detail
        self.client.force_authenticate(user=self.admin_user)
        url = reverse('organization-detail', kwargs={'pk': org2.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class AuthorizationTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        # Authorization org
        self.org = Organization.objects.create(
            customer_code='AUTHZ',
            customer_name='AuthZ Org',
            customer_industry='Services',
            financial_year_end_date=date.today(),
        )
        # Admin, Manager, Staff under same org
        self.admin = User.objects.create_user(
            email='authz_admin@test.com',
            username='authz_admin',
            password='testpass',
            organization=self.org,
            role='admin'
        )
        self.manager = User.objects.create_user(
            email='manager@test.com',
            username='manager',
            password='testpass',
            organization=self.org,
            role='manager'
        )
        self.staff = User.objects.create_user(
            email='staff@test.com',
            username='staff',
            password='testpass',
            organization=self.org,
            role='staff'
        )

    def test_admin_permissions(self):
        self.client.force_authenticate(user=self.admin)
        url = reverse('organizations:organization-users-list', kwargs={'org_pk': self.org.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_manager_permissions(self):
        self.client.force_authenticate(user=self.manager)
        url = reverse('organization-detail', kwargs={'pk': self.org.id})
        url = reverse('organizations:organization-detail', kwargs={'pk': self.org.id})
        response = self.client.patch(url, {'customer_name': 'Updated Name'})
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_staff_permissions(self):
        self.client.force_authenticate(user=self.staff)
        url = reverse('organizations:organization-settings', kwargs={'org_pk': self.org.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class OTPSecurityTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        # OTP tests org
        self.org = Organization.objects.create(
            customer_code='OTP_TEST',
            customer_name='OTP Test Org',
            customer_industry='Security',
            financial_year_end_date=date.today(),
        )
        self.user = User.objects.create_user(
            email='otpuser@test.com',
            username='otpuser',
            password='testpass',
            organization=self.org
        )

    def test_otp_required_endpoint(self):
        # First login without OTP
        login_url = reverse('user-login')
        data = {'email': 'otpuser@test.com', 'password': 'testpass'}
        response = self.client.post(login_url, data)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertIn('otp_required', response.data)

    def test_otp_verification_flow(self):
        # Create OTP record
        otp = self.user.otps.create(otp='123456', role='staff')
        # Verify OTP
        verify_url = reverse('users:verify-otp')
        data = {'otp': '123456'}
        self.client.force_authenticate(user=self.user)
        response = self.client.post(verify_url, data)
        otp.refresh_from_db()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(otp.is_verified)

    def test_max_otp_attempts(self):
        # Create OTP record
        otp = self.user.otps.create(otp='654321', role='staff')
        verify_url = reverse('users:verify-otp')
        data = {'otp': 'wrong'}
        self.client.force_authenticate(user=self.user)
        # Exceed max attempts
        for _ in range(3):
            response = self.client.post(verify_url, data)
        otp.refresh_from_db()
        self.assertEqual(otp.attempts, 3)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)