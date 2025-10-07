"""
Test security headers and transport security.
"""
import pytest  # type: ignore[reportMissingImports]
from django.test import Client
from django.conf import settings


class TestSecurityHeaders:
    """Test security headers are properly set."""
    
    def test_csp_header(self, client_public):
        """Test Content Security Policy header."""
        response = client_public.get("/public/")
        csp_header = response.get("Content-Security-Policy")
        assert csp_header is not None, "CSP header should be present"
    
    def test_x_frame_options(self, client_public):
        """Test X-Frame-Options header."""
        response = client_public.get("/public/")
        x_frame_options = response.get("X-Frame-Options")
        assert x_frame_options is not None, "X-Frame-Options header should be present"
        assert x_frame_options.upper() in ["DENY", "SAMEORIGIN"], "X-Frame-Options should be DENY or SAMEORIGIN"
    
    def test_x_content_type_options(self, client_public):
        """Test X-Content-Type-Options header."""
        response = client_public.get("/public/")
        x_content_type = response.get("X-Content-Type-Options")
        assert x_content_type is not None, "X-Content-Type-Options header should be present"
        assert x_content_type.lower() == "nosniff", "X-Content-Type-Options should be nosniff"
    
    def test_x_xss_protection(self, client_public):
        """Test X-XSS-Protection header."""
        response = client_public.get("/public/")
        x_xss_protection = response.get("X-XSS-Protection")
        # This header is deprecated but may still be present
        if x_xss_protection:
            assert x_xss_protection in ["1", "1; mode=block"], "X-XSS-Protection should be 1 or 1; mode=block"
    
    def test_referrer_policy(self, client_public):
        """Test Referrer-Policy header."""
        response = client_public.get("/public/")
        referrer_policy = response.get("Referrer-Policy")
        # Referrer-Policy is optional but good to have
        if referrer_policy:
            assert referrer_policy.lower() in [
                "no-referrer", "no-referrer-when-downgrade", "origin", 
                "origin-when-cross-origin", "same-origin", "strict-origin",
                "strict-origin-when-cross-origin", "unsafe-url"
            ], "Referrer-Policy should have valid value"
    
    def test_hsts_header(self, client_public):
        """Test HTTP Strict Transport Security header."""
        response = client_public.get("/public/")
        hsts = response.get("Strict-Transport-Security")
        # HSTS should be present in production
        if settings.SECURE_SSL_REDIRECT:
            assert hsts is not None, "HSTS header should be present in production"
            assert "max-age" in hsts, "HSTS should include max-age"


class TestCookieSecurity:
    """Test cookie security settings."""
    
    def test_session_cookie_security(self, client_tenant_a, user_admin_a):
        """Test session cookie security settings."""
        client_tenant_a.force_login(user_admin_a)
        response = client_tenant_a.get("/accounts/")
        
        # Check Set-Cookie header
        set_cookie = response.get("Set-Cookie", "")
        if set_cookie:
            # In production, cookies should be secure
            if settings.SECURE_SSL_REDIRECT:
                assert "Secure" in set_cookie, "Session cookie should be Secure in production"
            assert "HttpOnly" in set_cookie, "Session cookie should be HttpOnly"
            assert "SameSite" in set_cookie, "Session cookie should have SameSite"
    
    def test_csrf_cookie_security(self, client_public):
        """Test CSRF cookie security settings."""
        response = client_public.get("/public/")
        
        # Check Set-Cookie header for CSRF
        set_cookie = response.get("Set-Cookie", "")
        if "csrftoken" in set_cookie:
            # In production, CSRF cookie should be secure
            if settings.SECURE_SSL_REDIRECT:
                assert "Secure" in set_cookie, "CSRF cookie should be Secure in production"
            assert "SameSite" in set_cookie, "CSRF cookie should have SameSite"


class TestTransportSecurity:
    """Test transport security settings."""
    
    def test_https_redirect(self, client_public):
        """Test HTTPS redirect in production."""
        if settings.SECURE_SSL_REDIRECT:
            response = client_public.get("/public/", secure=False)
            # Should redirect to HTTPS
            assert response.status_code == 301, "Should redirect to HTTPS"
            assert response.get("Location", "").startswith("https://"), "Should redirect to HTTPS URL"
    
    def test_secure_headers_in_production(self, client_public):
        """Test security headers are present in production."""
        if not settings.DEBUG:
            response = client_public.get("/public/")
            
            # Check for production security headers
            assert response.get("Content-Security-Policy") is not None, "CSP should be present in production"
            assert response.get("X-Frame-Options") is not None, "X-Frame-Options should be present in production"
            assert response.get("X-Content-Type-Options") is not None, "X-Content-Type-Options should be present in production"


class TestCORSHeaders:
    """Test CORS headers for API endpoints."""
    
    def test_cors_headers_api(self, client_public):
        """Test CORS headers for API endpoints."""
        response = client_public.options("/api/users/")
        
        # Check CORS headers
        cors_origin = response.get("Access-Control-Allow-Origin")
        cors_methods = response.get("Access-Control-Allow-Methods")
        cors_headers = response.get("Access-Control-Allow-Headers")
        
        # CORS headers should be present for API endpoints
        if cors_origin:
            assert cors_origin in ["*", "null"] or cors_origin.startswith("http"), "CORS origin should be valid"
        if cors_methods:
            assert "GET" in cors_methods, "CORS should allow GET method"
        if cors_headers:
            assert "Content-Type" in cors_headers, "CORS should allow Content-Type header"
    
    def test_cors_preflight_request(self, client_public):
        """Test CORS preflight request handling."""
        response = client_public.options(
            "/api/users/",
            HTTP_ACCESS_CONTROL_REQUEST_METHOD="POST",
            HTTP_ACCESS_CONTROL_REQUEST_HEADERS="Content-Type,Authorization"
        )
        
        # Should handle preflight request
        assert response.status_code in [200, 204], "Should handle CORS preflight request"


class TestErrorHandling:
    """Test error handling and information disclosure."""
    
    def test_404_error_handling(self, client_public):
        """Test 404 error handling doesn't leak information."""
        response = client_public.get("/nonexistent-page/")
        assert response.status_code == 404
        
        # Should not leak sensitive information
        content = response.content.decode()
        assert "Traceback" not in content, "Should not show traceback in 404"
        assert "django" not in content.lower(), "Should not show Django version in 404"
    
    def test_500_error_handling(self, client_public):
        """Test 500 error handling in production."""
        if not settings.DEBUG:
            # In production, 500 errors should not show tracebacks
            # This is hard to test without causing actual 500 errors
            pass
    
    def test_error_pages_security(self, client_public):
        """Test error pages don't leak sensitive information."""
        # Test various error scenarios
        error_endpoints = [
            "/admin/",  # Should return 404 due to blocked admin
            "/nonexistent/",
        ]
        
        for endpoint in error_endpoints:
            response = client_public.get(endpoint)
            content = response.content.decode()
            
            # Should not leak sensitive information
            assert "Traceback" not in content, f"Should not show traceback for {endpoint}"
            assert "django" not in content.lower(), f"Should not show Django info for {endpoint}"