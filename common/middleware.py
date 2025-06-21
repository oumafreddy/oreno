# C:\Users\ouma.fred\Desktop\GRC\oreno\common\middleware.py

from django.conf import settings
from django.shortcuts import redirect
from django.urls import reverse
from django.http import JsonResponse
import secrets

class LoginRequiredMiddleware:
    """
    Middleware that forces a user to be logged in to view any page except a defined whitelist.
    
    Configure settings.LOGIN_REQUIRED_EXEMPT_URLS in your settings file to provide a list
    of URLs (or URL names) that should be exempt from authentication (e.g. login, signup pages).
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
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
    Handles:
      - htmx (HX-Request header)
      - XMLHttpRequest (x-requested-with)
      - fetch/axios (Accept: application/json)
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
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
