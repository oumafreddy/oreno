# apps/users/middleware.py

from django.shortcuts import redirect
from django.urls import reverse
from django.contrib import messages
from django.utils.translation import gettext_lazy as _
from django.conf import settings
import logging

logger = logging.getLogger(__name__)


class FirstTimeSetupMiddleware:
    """
    Middleware that enforces first-time setup completion for users who require it.
    
    This middleware ensures that users who need to complete first-time setup
    (OTP verification and password setup) cannot access any app features until
    they successfully complete the setup process.
    
    IMPORTANT: This middleware only applies to tenant sites (e.g., org001.localhost:8000),
    NOT to the public site (127.0.0.1:8000 or localhost:8000).
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        # Only check authenticated users
        if not request.user.is_authenticated:
            return self.get_response(request)
        
        # Check if this is a public site (no tenant context)
        # Public sites should not enforce first-time setup
        if not hasattr(request, 'tenant') or request.tenant is None:
            return self.get_response(request)
        
        # Define URLs that are exempt from first-time setup check
        exempt_urls = [
            '/accounts/login/',
            '/accounts/logout/',
            '/accounts/register/',
            '/accounts/password-reset/',
            '/accounts/password-reset/done/',
            '/accounts/password-reset/confirm/',
            '/accounts/password-reset/complete/',
            '/accounts/first-time-setup/',
            '/accounts/resend-otp-setup/',
            '/static/',
            '/media/',
            '/favicon.ico',
            '/admin/',  # Allow admin access for superusers
        ]
        
        # Check if current path is exempt
        current_path = request.path
        if any(current_path.startswith(url) for url in exempt_urls):
            return self.get_response(request)
        
        # Check if user requires first-time setup
        if hasattr(request.user, 'requires_first_time_setup') and request.user.requires_first_time_setup():
            # Log the attempt to bypass first-time setup
            logger.warning(
                f"User {request.user.email} attempted to access {current_path} "
                f"without completing first-time setup on tenant {request.tenant.name}"
            )
            
            # Clear any existing session data that might interfere
            if 'first_time_setup_user_id' not in request.session:
                request.session['first_time_setup_user_id'] = request.user.id
                request.session['first_time_setup_required'] = True
            
            # Add a message to inform the user
            messages.warning(
                request,
                _("Please complete your account setup before accessing the application.")
            )
            
            # Redirect to first-time setup
            return redirect('users:first-time-setup')
        
        return self.get_response(request)


class FirstTimeSetupSessionMiddleware:
    """
    Middleware that manages first-time setup session state.
    
    This middleware ensures that first-time setup sessions are properly
    maintained and cleaned up when appropriate.
    
    IMPORTANT: This middleware only applies to tenant sites, NOT to the public site.
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        # Only process authenticated users on tenant sites
        if (request.user.is_authenticated and 
            hasattr(request, 'tenant') and request.tenant is not None):
            
            # Check if user has completed first-time setup
            if (hasattr(request.user, 'is_first_time_setup_complete') and 
                request.user.is_first_time_setup_complete):
                
                # Clean up first-time setup session data
                if 'first_time_setup_user_id' in request.session:
                    del request.session['first_time_setup_user_id']
                if 'first_time_setup_required' in request.session:
                    del request.session['first_time_setup_required']
        
        return self.get_response(request)
