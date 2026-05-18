# common/tests/test_middleware.py

from django.test import TestCase, RequestFactory
from django.contrib.auth import get_user_model
from django.http import HttpResponseRedirect, JsonResponse

from common.middleware import LoginRequiredMiddleware, AjaxLoginRequiredMiddleware, SecurityMiddleware

User = get_user_model()


class MiddlewareTests(TestCase):
    """Test cases for middleware behavior on public vs tenant sites"""
    
    def setUp(self):
        self.factory = RequestFactory()
    
    def get_request_with_tenant(self, path="/", tenant=None):
        """Helper method to create a request with tenant context"""
        request = self.factory.get(path)
        request.user = None  # Unauthenticated user
        request.tenant = tenant
        return request
    
    def test_login_required_middleware_allows_public_site(self):
        """Test that LoginRequiredMiddleware allows access on public sites"""
        middleware = LoginRequiredMiddleware(lambda req: None)
        request = self.get_request_with_tenant("/", tenant=None)  # Public site
        
        response = middleware(request)
        
        # Should not redirect (allow access on public sites)
        self.assertNotIsInstance(response, HttpResponseRedirect)
    
    def test_login_required_middleware_blocks_tenant_site(self):
        """Test that LoginRequiredMiddleware blocks access on tenant sites"""
        middleware = LoginRequiredMiddleware(lambda req: None)
        request = self.get_request_with_tenant("/", tenant="test_tenant")  # Tenant site
        
        response = middleware(request)
        
        # Should redirect to login
        self.assertIsInstance(response, HttpResponseRedirect)
        self.assertEqual(response.url, "/accounts/login/")
    
    def test_ajax_login_required_middleware_allows_public_site(self):
        """Test that AjaxLoginRequiredMiddleware allows access on public sites"""
        middleware = AjaxLoginRequiredMiddleware(lambda req: None)
        request = self.get_request_with_tenant("/", tenant=None)  # Public site
        request.headers = {'HX-Request': 'true'}  # Simulate HTMX request
        
        response = middleware(request)
        
        # Should not return 401 (allow access on public sites)
        self.assertNotIsInstance(response, JsonResponse)
    
    def test_ajax_login_required_middleware_blocks_tenant_site(self):
        """Test that AjaxLoginRequiredMiddleware blocks access on tenant sites"""
        middleware = AjaxLoginRequiredMiddleware(lambda req: None)
        request = self.get_request_with_tenant("/", tenant="test_tenant")  # Tenant site
        request.headers = {'HX-Request': 'true'}  # Simulate HTMX request
        
        response = middleware(request)
        
        # Should return 401 for AJAX requests
        self.assertIsInstance(response, JsonResponse)
        self.assertEqual(response.status_code, 401)


class SecurityMiddlewareTests(TestCase):
    """Regression tests for attack pattern detection false positives."""

    def setUp(self):
        self.factory = RequestFactory()
        self.middleware = SecurityMiddleware(lambda req: None)

    def test_business_text_in_post_not_flagged_as_attack(self):
        """
        Ensure normal multiline action-plan text is not treated as SQLi/XSS.
        This guards against false positives causing 400/403 lockouts.
        """
        payload = {
            "action_plan": (
                "1. Develop and have leadership endorsement on a comprehensive "
                "stakeholders selection criteria - Project manager and TRCS SG\n"
                "2. Stakeholders mapping and developing an engagement plan\n"
                "3. Undertake coalition building workshop"
            )
        }
        request = self.factory.post("/risk/risks/4/update/", data=payload)
        self.assertFalse(self.middleware._contains_attack_patterns(request))
