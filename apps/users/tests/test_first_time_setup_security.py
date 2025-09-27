# apps/users/tests/test_first_time_setup_security.py

from django.test import TestCase, RequestFactory
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.contrib.sessions.middleware import SessionMiddleware
from django.contrib.auth.middleware import AuthenticationMiddleware
from django.contrib.messages.middleware import MessageMiddleware
from django.contrib.messages.storage.fallback import FallbackStorage
from django.http import HttpResponseRedirect

from users.middleware import FirstTimeSetupMiddleware, FirstTimeSetupSessionMiddleware
from users.models import OTP
from organizations.models import Organization

User = get_user_model()


class FirstTimeSetupSecurityTests(TestCase):
    """Test cases for first-time setup security middleware"""
    
    def setUp(self):
        self.factory = RequestFactory()
        
        # Create test organization
        self.org = Organization.objects.create(
            name="Test Organization",
            code="TEST001",
            schema_name="test_org"
        )
        
        # Create test user who needs first-time setup
        self.user = User.objects.create_user(
            email="test@example.com",
            username="testuser",
            password="testpass123",
            organization=self.org,
            is_first_time_setup_complete=False,
            is_admin_created=True
        )
        
        # Create test user who has completed setup
        self.completed_user = User.objects.create_user(
            email="completed@example.com",
            username="completeduser",
            password="testpass123",
            organization=self.org,
            is_first_time_setup_complete=True
        )
        
        # Create OTP for the test user
        self.otp = OTP.objects.create(
            user=self.user,
            otp="123456"
        )
    
    def get_request_with_user(self, user, path="/"):
        """Helper method to create a request with an authenticated user"""
        request = self.factory.get(path)
        request.user = user
        
        # Add session middleware
        middleware = SessionMiddleware(lambda req: None)
        middleware.process_request(request)
        request.session.save()
        
        # Add authentication middleware
        auth_middleware = AuthenticationMiddleware(lambda req: None)
        auth_middleware.process_request(request)
        
        # Add messages middleware
        messages_middleware = MessageMiddleware(lambda req: None)
        messages_middleware.process_request(request)
        
        return request
    
    def test_middleware_allows_first_time_setup_page(self):
        """Test that middleware allows access to first-time setup page"""
        middleware = FirstTimeSetupMiddleware(lambda req: None)
        request = self.get_request_with_user(self.user, "/accounts/first-time-setup/")
        
        response = middleware(request)
        
        # Should not redirect (allow access)
        self.assertNotIsInstance(response, HttpResponseRedirect)
    
    def test_middleware_allows_login_page(self):
        """Test that middleware allows access to login page"""
        middleware = FirstTimeSetupMiddleware(lambda req: None)
        request = self.get_request_with_user(self.user, "/accounts/login/")
        
        response = middleware(request)
        
        # Should not redirect (allow access)
        self.assertNotIsInstance(response, HttpResponseRedirect)
    
    def test_middleware_blocks_home_page_for_incomplete_setup(self):
        """Test that middleware blocks home page for users who haven't completed setup"""
        middleware = FirstTimeSetupMiddleware(lambda req: None)
        request = self.get_request_with_user(self.user, "/")
        request.tenant = self.org  # Simulate tenant site
        
        response = middleware(request)
        
        # Should redirect to first-time setup
        self.assertIsInstance(response, HttpResponseRedirect)
        self.assertEqual(response.url, "/accounts/first-time-setup/")
    
    def test_middleware_blocks_app_features_for_incomplete_setup(self):
        """Test that middleware blocks app features for users who haven't completed setup"""
        middleware = FirstTimeSetupMiddleware(lambda req: None)
        request = self.get_request_with_user(self.user, "/audit/")
        request.tenant = self.org  # Simulate tenant site
        
        response = middleware(request)
        
        # Should redirect to first-time setup
        self.assertIsInstance(response, HttpResponseRedirect)
        self.assertEqual(response.url, "/accounts/first-time-setup/")
    
    def test_middleware_allows_access_for_completed_setup(self):
        """Test that middleware allows access for users who have completed setup"""
        middleware = FirstTimeSetupMiddleware(lambda req: None)
        request = self.get_request_with_user(self.completed_user, "/")
        
        response = middleware(request)
        
        # Should not redirect (allow access)
        self.assertNotIsInstance(response, HttpResponseRedirect)
    
    def test_middleware_allows_static_files(self):
        """Test that middleware allows access to static files"""
        middleware = FirstTimeSetupMiddleware(lambda req: None)
        request = self.get_request_with_user(self.user, "/static/css/style.css")
        
        response = middleware(request)
        
        # Should not redirect (allow access)
        self.assertNotIsInstance(response, HttpResponseRedirect)
    
    def test_middleware_allows_admin_access(self):
        """Test that middleware allows admin access"""
        middleware = FirstTimeSetupMiddleware(lambda req: None)
        request = self.get_request_with_user(self.user, "/admin/")
        
        response = middleware(request)
        
        # Should not redirect (allow access)
        self.assertNotIsInstance(response, HttpResponseRedirect)
    
    def test_session_middleware_cleans_up_completed_setup(self):
        """Test that session middleware cleans up session data for completed users"""
        session_middleware = FirstTimeSetupSessionMiddleware(lambda req: None)
        request = self.get_request_with_user(self.completed_user, "/")
        request.tenant = self.org  # Simulate tenant site
        
        # Add session data that should be cleaned up
        request.session['first_time_setup_user_id'] = self.completed_user.id
        request.session['first_time_setup_required'] = True
        
        response = session_middleware(request)
        
        # Session data should be cleaned up
        self.assertNotIn('first_time_setup_user_id', request.session)
        self.assertNotIn('first_time_setup_required', request.session)
    
    def test_middleware_handles_unauthenticated_user(self):
        """Test that middleware handles unauthenticated users properly"""
        middleware = FirstTimeSetupMiddleware(lambda req: None)
        request = self.factory.get("/")
        request.user = None  # Unauthenticated user
        
        response = middleware(request)
        
        # Should not redirect (allow access - handled by login middleware)
        self.assertNotIsInstance(response, HttpResponseRedirect)
    
    def test_middleware_allows_public_site_access(self):
        """Test that middleware allows access on public sites (no tenant)"""
        middleware = FirstTimeSetupMiddleware(lambda req: None)
        request = self.get_request_with_user(self.user, "/")
        request.tenant = None  # Simulate public site (no tenant)
        
        response = middleware(request)
        
        # Should not redirect (allow access on public sites)
        self.assertNotIsInstance(response, HttpResponseRedirect)
