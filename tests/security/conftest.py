"""
Pytest configuration for security tests.
"""
import os
import sys
import uuid
import django
from django.conf import settings

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

# Configure Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.tenants')

# Setup Django
django.setup()

import pytest
from django.test import TestCase, Client
from django.test.utils import override_settings
from django.contrib.auth import get_user_model
from organizations.models import Organization, Domain  # type: ignore[reportMissingImports]
from users.models import Profile, OTP  # type: ignore[reportMissingImports]

User = get_user_model()


@pytest.fixture
def client():
    """Django test client fixture."""
    return Client()


@pytest.fixture
def client_public():
    """Public client using public URLConf."""
    with override_settings(ROOT_URLCONF='config.urls_public'):
        yield Client()


# Tenant fixtures (matching test expectations)
@pytest.fixture
def tenant_a():
    """Create tenant A for testing."""
    unique = uuid.uuid4().hex[:8]
    org = Organization.objects.create(
        name=f"Tenant A {unique}",
        code=f"TENANT_A_{unique}",
        schema_name=f"tenant_a_{unique}",
        is_active=True
    )
    return org


@pytest.fixture
def domain_a(tenant_a):
    """Primary domain for tenant A used by middleware resolution."""
    host = f"org-{tenant_a.code.lower()}.localhost"
    return Domain.objects.create(domain=host, tenant=tenant_a, is_primary=True)


@pytest.fixture
def tenant_b():
    """Create tenant B for testing."""
    unique = uuid.uuid4().hex[:8]
    org = Organization.objects.create(
        name=f"Tenant B {unique}", 
        code=f"TENANT_B_{unique}",
        schema_name=f"tenant_b_{unique}",
        is_active=True
    )
    return org


@pytest.fixture
def domain_b(tenant_b):
    """Primary domain for tenant B used by middleware resolution."""
    host = f"org-{tenant_b.code.lower()}.localhost"
    return Domain.objects.create(domain=host, tenant=tenant_b, is_primary=True)


@pytest.fixture
def host_a(domain_a):
    return domain_a.domain


@pytest.fixture
def host_b(domain_b):
    return domain_b.domain


# User fixtures (matching test expectations)
@pytest.fixture
def user_admin_a(tenant_a):
    """Create admin user for tenant A."""
    unique = uuid.uuid4().hex[:8]
    user = User.objects.create_user(
        username=f"fredouma@oreno.tech+{unique}",
        email="fredouma@oreno.tech",
        password="adminpass123",
        first_name="Admin",
        last_name="A",
        organization=tenant_a,
        is_staff=True,
        is_superuser=True
    )
    return user


@pytest.fixture
def user_staff_a(tenant_a):
    """Create staff user for tenant A."""
    unique = uuid.uuid4().hex[:8]
    user = User.objects.create_user(
        username=f"staff_a@example.com+{unique}",
        email="staff_a@example.com",
        password="staffpass123",
        first_name="Staff",
        last_name="A",
        organization=tenant_a,
        is_staff=True
    )
    return user


@pytest.fixture
def user_manager_a(tenant_a):
    """Create manager user for tenant A."""
    unique = uuid.uuid4().hex[:8]
    user = User.objects.create_user(
        username=f"manager_a@example.com+{unique}",
        email="manager_a@example.com",
        password="managerpass123",
        first_name="Manager",
        last_name="A",
        organization=tenant_a
    )
    return user


@pytest.fixture
def user_admin_b(tenant_b):
    """Create admin user for tenant B."""
    unique = uuid.uuid4().hex[:8]
    user = User.objects.create_user(
        username=f"admin_b@example.com+{unique}",
        email="admin_b@example.com",
        password="adminpass123",
        first_name="Admin",
        last_name="B",
        organization=tenant_b,
        is_staff=True,
        is_superuser=True
    )
    return user


# Client fixtures (matching test expectations)
@pytest.fixture
def client_tenant_a(tenant_a, domain_a):
    """Client for tenant A."""
    return Client()


@pytest.fixture
def client_tenant_b(tenant_b, domain_b):
    """Client for tenant B."""
    return Client()


# Auth header fixtures
@pytest.fixture
def auth_headers_admin_a(user_admin_a):
    """Auth headers for admin user A."""
    from rest_framework_simplejwt.tokens import RefreshToken
    refresh = RefreshToken.for_user(user_admin_a)
    return {
        'HTTP_AUTHORIZATION': f'Bearer {refresh.access_token}'
    }


@pytest.fixture
def auth_headers_staff_a(user_staff_a):
    """Auth headers for staff user A."""
    from rest_framework_simplejwt.tokens import RefreshToken
    refresh = RefreshToken.for_user(user_staff_a)
    return {
        'HTTP_AUTHORIZATION': f'Bearer {refresh.access_token}'
    }


# Legacy fixtures (for backward compatibility)
@pytest.fixture
def test_organization():
    """Create a test organization."""
    org = Organization.objects.create(
        name="Test Organization",
        code="TEST",
        schema_name="test",
        is_active=True
    )
    return org


@pytest.fixture
def test_domain(test_organization):
    """Create a test domain for the organization."""
    domain = Domain.objects.create(
        domain="test.localhost",
        tenant=test_organization,
        is_primary=True
    )
    return domain


@pytest.fixture
def test_user(test_organization):
    """Create a test user."""
    unique = uuid.uuid4().hex[:8]
    user = User.objects.create_user(
        username=f"test@example.com+{unique}",
        email="test@example.com",
        password="testpass123",
        first_name="Test",
        last_name="User",
        organization=test_organization
    )
    return user


@pytest.fixture
def test_admin_user(test_organization):
    """Create a test admin user."""
    unique = uuid.uuid4().hex[:8]
    user = User.objects.create_user(
        username=f"admin@example.com+{unique}",
        email="admin@example.com",
        password="adminpass123",
        first_name="Admin",
        last_name="User",
        organization=test_organization,
        is_staff=True,
        is_superuser=True
    )
    return user


@pytest.fixture
def test_user_profile(test_user):
    """Create a test user profile."""
    profile = Profile.objects.create(
        user=test_user,
        phone_number="+1234567890",
        department="IT",
        job_title="Developer"
    )
    return profile


@pytest.fixture
def test_otp(test_user):
    """Create a test OTP."""
    otp = OTP.objects.create(
        user=test_user,
        code="123456",
        purpose="login"
    )
    return otp


@pytest.fixture
def authenticated_client(client, test_user):
    """Client with authenticated user."""
    client.force_login(test_user)
    return client


@pytest.fixture
def admin_client(client, test_admin_user):
    """Client with authenticated admin user."""
    client.force_login(test_admin_user)
    return client


@pytest.fixture
def second_organization():
    """Create a second test organization for isolation tests."""
    org = Organization.objects.create(
        name="Second Organization",
        code="SECOND",
        schema_name="second",
        is_active=True
    )
    return org


@pytest.fixture
def second_user(second_organization):
    """Create a user in the second organization."""
    unique = uuid.uuid4().hex[:8]
    user = User.objects.create_user(
        username=f"second@example.com+{unique}",
        email="second@example.com",
        password="secondpass123",
        first_name="Second",
        last_name="User",
        organization=second_organization
    )
    return user


@pytest.fixture
def second_authenticated_client(client, second_user):
    """Client with authenticated user from second organization."""
    client.force_login(second_user)
    return client


# Test data fixtures
@pytest.fixture
def sample_form_data():
    """Sample form data for testing."""
    return {
        'name': 'Test Item',
        'description': 'Test description',
        'email': 'test@example.com',
        'phone': '+1234567890'
    }


@pytest.fixture
def malicious_input_data():
    """Malicious input data for testing."""
    return {
        'script': '<script>alert("xss")</script>',
        'sql': "'; DROP TABLE users; --",
        'path_traversal': '../../../etc/passwd',
        'command_injection': '; rm -rf /',
        'html': '<img src=x onerror=alert(1)>',
        'javascript': 'javascript:alert(1)'
    }


@pytest.fixture
def large_input_data():
    """Large input data for testing limits."""
    return {
        'large_text': 'A' * 10000,
        'large_number': 999999999999999999,
        'special_chars': '!@#$%^&*()_+-=[]{}|;:,.<>?'
    }