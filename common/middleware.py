# C:\Users\ouma.fred\Desktop\GRC\oreno\common\middleware.py

from django.conf import settings
from django.shortcuts import redirect
from django.urls import reverse
from django.utils.deprecation import MiddlewareMixin

class LoginRequiredMiddleware(MiddlewareMixin):
    """
    Middleware that forces a user to be logged in to view any page except a defined whitelist.
    
    Configure settings.LOGIN_REQUIRED_EXEMPT_URLS in your settings file to provide a list
    of URLs (or URL names) that should be exempt from authentication (e.g. login, signup pages).
    """
    def process_request(self, request):
        # List of URL paths to exempt from login requirement
        exempt_urls = getattr(settings, "LOGIN_REQUIRED_EXEMPT_URLS", [])
        # Alternatively, you could use URL names here and reverse them if desired.

        # If the requested path is in the exempt list, do nothing.
        if any(request.path.startswith(url) for url in exempt_urls):
            return None
        
        # If user is not authenticated, redirect to the LOGIN_URL (configured in settings)
        if not request.user.is_authenticated:
            return redirect(settings.LOGIN_URL)
        
        # Otherwise, continue processing the request.
        return None
