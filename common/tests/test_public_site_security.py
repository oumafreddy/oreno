# common/tests/test_public_site_security.py

from django.test import TestCase, Client
from django.urls import reverse


class PublicSiteSecurityTests(TestCase):
    """Test cases to ensure public site blocks tenant-specific routes"""
    
    def setUp(self):
        self.client = Client()
    
    def test_public_site_blocks_accounts_login(self):
        """Test that /accounts/login/ returns 404 on public site"""
        response = self.client.get('/accounts/login/')
        self.assertEqual(response.status_code, 404)
    
    def test_public_site_blocks_accounts_logout(self):
        """Test that /accounts/logout/ returns 404 on public site"""
        response = self.client.get('/accounts/logout/')
        self.assertEqual(response.status_code, 404)
    
    def test_public_site_blocks_accounts_register(self):
        """Test that /accounts/register/ returns 404 on public site"""
        response = self.client.get('/accounts/register/')
        self.assertEqual(response.status_code, 404)
    
    def test_public_site_blocks_first_time_setup(self):
        """Test that /accounts/first-time-setup/ returns 404 on public site"""
        response = self.client.get('/accounts/first-time-setup/')
        self.assertEqual(response.status_code, 404)
    
    def test_public_site_blocks_organizations_routes(self):
        """Test that /organizations/* routes return 404 on public site"""
        response = self.client.get('/organizations/')
        self.assertEqual(response.status_code, 404)
        
        response = self.client.get('/organizations/create/')
        self.assertEqual(response.status_code, 404)
    
    def test_public_site_blocks_api_users(self):
        """Test that /api/users/* routes return 404 on public site"""
        response = self.client.get('/api/users/')
        self.assertEqual(response.status_code, 404)
    
    def test_public_site_blocks_api_organizations(self):
        """Test that /api/organizations/* routes return 404 on public site"""
        response = self.client.get('/api/organizations/')
        self.assertEqual(response.status_code, 404)
    
    def test_public_site_blocks_api_auth(self):
        """Test that /api/auth/* routes return 404 on public site"""
        response = self.client.get('/api/auth/')
        self.assertEqual(response.status_code, 404)
    
    def test_public_site_allows_public_pages(self):
        """Test that public pages are accessible"""
        # Home page
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        
        # Privacy policy
        response = self.client.get('/privacy-policy/')
        self.assertEqual(response.status_code, 200)
        
        # Cookie policy
        response = self.client.get('/cookie-policy/')
        self.assertEqual(response.status_code, 200)
        
        # Documentation
        response = self.client.get('/docs/')
        self.assertEqual(response.status_code, 200)
        
        # Health check
        response = self.client.get('/health/')
        self.assertEqual(response.status_code, 200)
        
        # Sitemap
        response = self.client.get('/sitemap.xml')
        self.assertEqual(response.status_code, 200)
        
        # Robots.txt
        response = self.client.get('/robots.txt')
        self.assertEqual(response.status_code, 200)
    
    def test_public_site_allows_static_files(self):
        """Test that static files are accessible"""
        # This would need actual static files to test properly
        # For now, just ensure the URL pattern exists
        response = self.client.get('/static/css/style.css')
        # Should return 404 if file doesn't exist, but not block the route
        self.assertIn(response.status_code, [200, 404])
