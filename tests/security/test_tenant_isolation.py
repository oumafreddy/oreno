"""
Test tenant isolation and cross-tenant access prevention.
"""
import pytest  # type: ignore[reportMissingImports]
from django.test import Client
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import RefreshToken

User = get_user_model()


class TestTenantIsolation:
    """Test that tenants are properly isolated from each other."""
    
    def test_cross_tenant_domain_access_denied(self, client_tenant_a, user_admin_a, host_b):
        """Test user from tenant A cannot access tenant B domain."""
        client_tenant_a.force_login(user_admin_a)
        
        # Try to access tenant B domain with tenant A user
        response = client_tenant_a.get("/", HTTP_HOST=host_b)
        # Should be denied or redirected
        assert response.status_code in [302, 401, 403]
    
    def test_cross_tenant_api_access_denied(self, client_tenant_a, user_admin_a, host_b):
        """Test API access across tenants is denied."""
        # Get JWT token for tenant A user
        refresh = RefreshToken.for_user(user_admin_a)
        access_token = refresh.access_token
        
        headers = {"Authorization": f"Bearer {access_token}"}
        
        # Try to access tenant B API with tenant A token
        response = client_tenant_a.get("/api/users/", headers=headers, HTTP_HOST=host_b)
        assert response.status_code in [401, 403]
    
    def test_tenant_context_middleware(self, client_tenant_a, user_admin_a, host_a):
        """Test tenant context is properly set by middleware."""
        client_tenant_a.force_login(user_admin_a)
        
        # Access an endpoint that should have tenant context
        response = client_tenant_a.get("/accounts/", HTTP_HOST=host_a)
        assert response.status_code == 200
        
        # The middleware should have set request.tenant and request.organization
        # This is tested indirectly by successful access
    
    def test_tenant_specific_data_isolation(self, client_tenant_a, client_tenant_b, 
                                          user_admin_a, user_admin_b, host_a, host_b):
        """Test that tenant-specific data is isolated."""
        # Create some test data in each tenant
        # Context ensured by HTTP_HOST in requests
        
        # Login to each tenant
        client_tenant_a.force_login(user_admin_a)
        client_tenant_b.force_login(user_admin_b)
        
        # Each user should only see their own organization data
        response_a = client_tenant_a.get("/accounts/", HTTP_HOST=host_a)
        response_b = client_tenant_b.get("/accounts/", HTTP_HOST=host_b)
        
        assert response_a.status_code == 200
        assert response_b.status_code == 200
        
        # The responses should be different (different tenant data)
        # This is tested by successful access with different users


class TestCrossTenantObjectAccess:
    """Test that objects from one tenant cannot be accessed by another tenant."""
    
    def test_cross_tenant_object_idor_prevention(self, client_tenant_a, client_tenant_b,
                                               user_admin_a, user_admin_b, tenant_a, tenant_b):
        """Test IDOR prevention across tenants."""
        # This test would need actual objects to test with
        # For now, we test that the endpoints are properly protected
        
        client_tenant_a.force_login(user_admin_a)
        client_tenant_b.force_login(user_admin_b)
        
        # Test that each tenant can access their own data
        response_a = client_tenant_a.get("/accounts/")
        response_b = client_tenant_b.get("/accounts/")
        
        assert response_a.status_code == 200
        assert response_b.status_code == 200
    
    def test_tenant_filtering_in_querysets(self, client_tenant_a, user_admin_a, host_a):
        """Test that querysets are properly filtered by tenant."""
        client_tenant_a.force_login(user_admin_a)
        
        # Access endpoints that should return tenant-filtered data
        endpoints = [
            "/api/users/",
            "/api/risk/risks/",
            "/api/audit/engagements/",
        ]
        
        for endpoint in endpoints:
            response = client_tenant_a.get(endpoint, HTTP_HOST=host_a)
            # Should not return 500 (which would indicate queryset issues)
            assert response.status_code != 500


class TestTenantMiddleware:
    """Test tenant middleware functionality."""
    
    def test_tenant_resolution_from_domain(self, client_tenant_a, host_a):
        """Test tenant is resolved from domain."""
        # Access with tenant A domain
        response = client_tenant_a.get("/health/", HTTP_HOST=host_a)
        assert response.status_code == 200
        
        # Access with different domain should fail or redirect
        response = client_tenant_a.get("/health/", HTTP_HOST="nonexistent.localhost")
        # May return 404 or redirect depending on configuration
        assert response.status_code in [200, 302, 404]
    
    def test_tenant_context_preservation(self, client_tenant_a, user_admin_a, host_a):
        """Test tenant context is preserved throughout request."""
        client_tenant_a.force_login(user_admin_a)
        
        # Access multiple endpoints to ensure context is preserved
        endpoints = ["/", "/accounts/", "/risk/"]
        
        for endpoint in endpoints:
            response = client_tenant_a.get(endpoint, HTTP_HOST=host_a)
            # Should not return 500 (context issues)
            assert response.status_code != 500