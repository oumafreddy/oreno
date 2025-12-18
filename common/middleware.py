# C:\Users\ouma.fred\Desktop\GRC\oreno\common\middleware.py

from django.conf import settings
from django.shortcuts import redirect
from django.urls import reverse
from django.http import JsonResponse
from django.core.cache import cache
import secrets
import re
import logging

class LoginRequiredMiddleware:
    """
    Middleware that forces a user to be logged in to view any page except a defined whitelist.
    
    IMPORTANT: This middleware only applies to tenant sites (e.g., org001.localhost:8000),
    NOT to the public site (127.0.0.1:8000 or localhost:8000).
    
    Configure settings.LOGIN_REQUIRED_EXEMPT_URLS in your settings file to provide a list
    of URLs (or URL names) that should be exempt from authentication (e.g. login, signup pages).
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Check if this is a public site (no tenant context)
        # Public sites should not enforce login requirements
        if not hasattr(request, 'tenant') or request.tenant is None:
            return self.get_response(request)
        
        # List of URL paths to exempt from login requirement
        exempt_urls = getattr(settings, "LOGIN_REQUIRED_EXEMPT_URLS", [])
        # Alternatively, you could use URL names here and reverse them if desired.

        # If the requested path is in the exempt list, do nothing.
        if any(request.path.startswith(url) for url in exempt_urls):
            return self.get_response(request)
        
        # If user is not authenticated, redirect to the LOGIN_URL (configured in settings)
        if not request.user.is_authenticated:
            return redirect(settings.LOGIN_URL)
        
        # Otherwise, continue processing the request.
        return self.get_response(request)

class AjaxLoginRequiredMiddleware:
    """
    Middleware that returns a JSON 401 for AJAX/htmx/fetch unauthenticated requests,
    instead of redirecting to the login page. This prevents JSON.parse errors in JS/htmx.
    
    IMPORTANT: This middleware only applies to tenant sites, NOT to the public site.
    
    Handles:
      - htmx (HX-Request header)
      - XMLHttpRequest (x-requested-with)
      - fetch/axios (Accept: application/json)
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Check if this is a public site (no tenant context)
        # Public sites should not enforce login requirements
        if not hasattr(request, 'tenant') or request.tenant is None:
            return self.get_response(request)
        
        if not request.user.is_authenticated:
            is_htmx = request.headers.get('HX-Request')
            is_ajax = request.headers.get('x-requested-with') == 'XMLHttpRequest'
            wants_json = 'application/json' in request.headers.get('Accept', '')
            if is_htmx or is_ajax or wants_json:
                return JsonResponse({'error': 'login_required'}, status=401)
        return self.get_response(request)


class CSPNonceMiddleware:
    """Attach a CSP nonce to the request and response. Allows external scripts in development, strict in production."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        import os
        nonce = secrets.token_hex(16)
        request.csp_nonce = nonce
        response = self.get_response(request)
        if getattr(settings, 'DEBUG', False):
            # Development: allow trusted CDNs for JS/CSS
            csp = (
                f"script-src 'self' 'nonce-{nonce}' 'unsafe-eval' "
                "https://cdn.jsdelivr.net https://code.jquery.com https://unpkg.com "
                "https://cdn.plot.ly https://www.googletagmanager.com; "
                "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net https://fonts.googleapis.com; "
                "font-src 'self' https://cdn.jsdelivr.net https://fonts.gstatic.com; "
                "img-src 'self' data: https://www.googletagmanager.com; "
                "connect-src 'self' https://cdn.plot.ly https://www.google-analytics.com; "
            )
        else:
            # Production: allow self, nonce, and necessary Plotly.js requirements
            csp = (
                f"script-src 'self' 'nonce-{nonce}' 'unsafe-eval'; "
                "style-src 'self' 'unsafe-inline'; "
                "font-src 'self'; "
                "img-src 'self' data:; "
                "connect-src 'self' https://cdn.plot.ly https://www.google-analytics.com;"
            )
        response['Content-Security-Policy'] = csp
        return response


class SecurityMiddleware:
    """
    Middleware to detect and block automated attack attempts.
    Can be disabled via SECURITY_MIDDLEWARE_ENABLED setting for testing.
    """
    logger = logging.getLogger('security.middleware')
    
    # SQL injection patterns
    SQL_INJECTION_PATTERNS = [
        r'(?i)(union.*select|select.*from|insert.*into|delete.*from|update.*set|drop.*table)',
        r'(?i)(or\s+\d+\s*=\s*\d+|and\s+\d+\s*=\s*\d+)',
        r'(?i)(sleep\s*\(|waitfor\s+delay|pg_sleep|benchmark\s*\()',
        r'(?i)(exec\s*\(|execute\s*\(|sp_executesql)',
        r'(?i)(xp_cmdshell|xp_regread|xp_dirtree)',
        r'(?i)(extractvalue|updatexml|exp\s*\(|gtid_subset)',
        r'(?i)(information_schema|sys\.|pg_catalog)',
        r'(?i)(char\s*\(|chr\s*\(|concat|cast\s*\()',
        r'(?i)(--\s*$|/\*|\*/|#\s*$)',
        r'(?i)(\'\s*(or|and)\s*\'|\"\s*(or|and)\s*\")',
    ]
    
    # XSS patterns
    XSS_PATTERNS = [
        r'(?i)(<script|javascript:|onerror=|onload=|onclick=)',
        r'(?i)(alert\s*\(|prompt\s*\(|confirm\s*\()',
        r'(?i)(eval\s*\(|expression\s*\()',
    ]
    
    # Path traversal patterns
    PATH_TRAVERSAL_PATTERNS = [
        r'(\.\./|\.\.\\|\.\.%2f|\.\.%5c)',
        r'(?i)(etc/passwd|boot\.ini|win\.ini)',
    ]
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        # Check if security middleware is enabled (can be disabled for testing)
        from django.conf import settings
        if not getattr(settings, 'SECURITY_MIDDLEWARE_ENABLED', True):
            return self.get_response(request)
        
        # Get client IP
        client_ip = self._get_client_ip(request)
        
        # Check rate limiting
        if self._is_rate_limited(client_ip):
            self.logger.warning(f"Rate limit exceeded for IP: {client_ip}")
            return JsonResponse(
                {'error': 'Rate limit exceeded. Please try again later.'},
                status=429
            )
        
        # Check for attack patterns in query parameters
        if self._contains_attack_patterns(request):
            # Increment attack counter
            cache_key = f'attack_count_{client_ip}'
            attack_count = cache.get(cache_key, 0) + 1
            cache.set(cache_key, attack_count, timeout=3600)  # 1 hour
            
            self.logger.warning(
                f"Attack pattern detected from IP {client_ip}: "
                f"{request.path}?{request.GET.urlencode()[:200]}"
            )
            
            # Block after 3 attempts
            if attack_count >= 3:
                cache.set(f'blocked_ip_{client_ip}', True, timeout=3600)  # Block for 1 hour
                self.logger.error(f"IP {client_ip} blocked due to repeated attack attempts")
                return JsonResponse(
                    {'error': 'Access denied'},
                    status=403
                )
            
            return JsonResponse(
                {'error': 'Invalid request'},
                status=400
            )
        
        # Check if IP is blocked
        if cache.get(f'blocked_ip_{client_ip}', False):
            return JsonResponse(
                {'error': 'Access denied'},
                status=403
            )
        
        return self.get_response(request)
    
    def _get_client_ip(self, request):
        """Get client IP address"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0].strip()
        else:
            ip = request.META.get('REMOTE_ADDR', 'unknown')
        return ip
    
    def _is_rate_limited(self, client_ip):
        """Check if IP has exceeded rate limit"""
        cache_key = f'rate_limit_{client_ip}'
        request_count = cache.get(cache_key, 0)
        
        # Allow 100 requests per minute
        if request_count >= 100:
            return True
        
        # Increment counter
        cache.set(cache_key, request_count + 1, timeout=60)
        return False
    
    def _contains_attack_patterns(self, request):
        """Check if request contains attack patterns"""
        # Check query parameters
        query_string = request.GET.urlencode().lower()
        if query_string:
            for pattern in self.SQL_INJECTION_PATTERNS + self.XSS_PATTERNS + self.PATH_TRAVERSAL_PATTERNS:
                if re.search(pattern, query_string):
                    return True
        
        # Check path
        path = request.path.lower()
        for pattern in self.SQL_INJECTION_PATTERNS + self.XSS_PATTERNS + self.PATH_TRAVERSAL_PATTERNS:
            if re.search(pattern, path):
                return True
        
        # Check POST data (if any)
        if request.method == 'POST' and request.POST:
            post_data = str(request.POST).lower()
            for pattern in self.SQL_INJECTION_PATTERNS + self.XSS_PATTERNS:
                if re.search(pattern, post_data):
                    return True
        
        return False
