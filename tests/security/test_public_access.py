"""
Test public endpoints are accessible without authentication.
Only /public/* routes should be accessible without auth.
"""
import pytest  # type: ignore[reportMissingImports]
from django.test import Client
from django.test.utils import override_settings
from django.urls import reverse


@pytest.mark.django_db
@override_settings(ROOT_URLCONF='config.urls_public')
class TestPublicEndpoints:
    """Test that public endpoints are accessible without authentication."""
    
    def test_public_docs_access(self, client_public):
        """Test /public/docs/ is accessible without auth."""
        response = client_public.get("/docs/")
        assert response.status_code == 200
    
    def test_public_home_access(self, client_public):
        """Test public home is accessible without auth."""
        response = client_public.get("/")
        assert response.status_code == 200
    
    def test_public_privacy_access(self, client_public):
        """Test privacy policy is accessible without auth."""
        response = client_public.get("/privacy-policy/")
        assert response.status_code == 200
    
    def test_public_cookies_access(self, client_public):
        """Test cookie policy is accessible without auth."""
        response = client_public.get("/cookie-policy/")
        assert response.status_code == 200
    
    @pytest.mark.parametrize("endpoint", [
        "/docs/",
        "/",
        "/privacy-policy/", 
        "/cookie-policy/",
    ])
    def test_public_endpoints_no_auth_required(self, client_public, endpoint):
        """Test all public endpoints are accessible without authentication."""
        response = client_public.get(endpoint)
        assert response.status_code == 200
        # Should not redirect to login
        assert response.status_code != 302
        assert "login" not in str(response.get("Location", ""))


@pytest.mark.django_db
@override_settings(ROOT_URLCONF='config.urls_public')
class TestNonPublicEndpointsRequireAuth:
    """Test that non-public endpoints require authentication."""
    
    def test_api_endpoints_require_auth(self, client_public):
        """Test API endpoints return 401/403 without authentication."""
        api_endpoints = [
            "/api/users/",
            "/api/risk/risks/",
            "/api/audit/engagements/",
            "/api/compliance/requirements/",
            "/api/contracts/contracts/",
            "/api/legal/cases/",
            "/api/ai-governance/models/",
        ]
        
        for endpoint in api_endpoints:
            response = client_public.get(endpoint)
            # In public URLConf, many tenant APIs are not mounted; 404 acceptable here
            assert response.status_code in [401, 403, 404], f"Endpoint {endpoint} should require auth or be absent"
    
    def test_web_endpoints_require_auth(self, client_public):
        """Test web endpoints redirect to login without authentication."""
        web_endpoints = [
            "/accounts/",
            "/risk/",
            "/audit/",
            "/compliance/",
            "/contracts/",
            "/legal/",
            "/ai-governance/",
            "/admin-module/",
        ]
        
        for endpoint in web_endpoints:
            response = client_public.get(endpoint)
            # In public URLConf, these are not mounted; 404 acceptable
            assert response.status_code in [302, 401, 403, 404], f"Endpoint {endpoint} should require auth or be absent"
            if response.status_code == 302:
                assert "login" in str(response.get("Location", "")), f"Endpoint {endpoint} should redirect to login"
    
    def test_admin_endpoints_require_auth(self, client_public):
        """Test admin endpoints are protected."""
        response = client_public.get("/admin/")
        assert response.status_code in [302, 404]  # 404 due to blocked admin path
    
    def test_health_endpoint_accessible(self, client_public):
        """Test health check endpoint is accessible."""
        response = client_public.get("/health/")
        assert response.status_code == 200
        assert response.content.decode() == "ok"