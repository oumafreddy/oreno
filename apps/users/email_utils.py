# apps/users/email_utils.py
"""
Email utilities for user-related notifications.
Provides robust, future-ready email services with proper error handling and logging.
"""

import logging
from django.conf import settings
from django.template.loader import render_to_string
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.core.mail import send_mail as django_send_mail
from core.utils import send_tenant_email
from .models import CustomUser

logger = logging.getLogger(__name__)


def send_password_change_notification(user, request=None, ip_address=None, user_agent=None):
    """
    Send password change notification email to user.
    
    This function is designed to be robust and future-ready:
    - Handles both tenant-specific and global email backends
    - Includes comprehensive security information
    - Provides fallback mechanisms
    - Logs all activities for audit trail
    - Supports future email preferences
    
    Args:
        user (CustomUser): The user whose password was changed
        request (HttpRequest, optional): Django request object for context
        ip_address (str, optional): IP address from which password was changed
        user_agent (str, optional): User agent string from request
        
    Returns:
        bool: True if email was sent successfully, False otherwise
    """
    if not user or not user.email:
        logger.warning(f"Password change notification skipped: invalid user or email")
        return False
    
    # Create email log entry
    from .models import UserEmailPreferences, EmailLog
    email_log = None
    
    try:
        email_log = EmailLog.log_email_attempt(
            user=user,
            email_type='password_change',
            recipient_email=user.email,
            subject=_('Password Changed - Security Notification'),
            ip_address=ip_address,
            user_agent=user_agent,
            context_data={'expiration_period': user.password_expiration_period}
        )
    except Exception as e:
        logger.warning(f"Could not create email log for {user.email}: {e}")
    
    # Check user's email preferences
    try:
        preferences = UserEmailPreferences.get_or_create_preferences(user)
        if not preferences.should_send_notification('password_change'):
            logger.info(f"Password change notification skipped for {user.email}: user has disabled notifications")
            if email_log:
                email_log.mark_skipped("User has disabled password change notifications")
            return True  # Return True since this is expected behavior
    except Exception as e:
        logger.warning(f"Could not check email preferences for {user.email}: {e}")
        # Continue with sending email if preferences check fails
    
    try:
        # Prepare email context
        context = {
            'user': user,
            'changed_at': timezone.now(),
            'site_name': getattr(settings, 'SITE_NAME', 'Oreno GRC'),
            'site_domain': getattr(settings, 'SITE_DOMAIN', ''),
            'login_url': f"{getattr(settings, 'SITE_URL', '')}/users/login/",
            'ip_address': ip_address,
            'user_agent': user_agent,
            'expiration_days': user.get_password_expiration_days(),
        }
        
        # Render email templates
        html_message = render_to_string('users/email/password_change_notification.html', context)
        plain_message = render_to_string('users/email/password_change_notification.txt', context)
        
        subject = _('Password Changed - Security Notification')
        
        # Determine recipients
        recipient_list = [user.email]
        
        # Log the attempt
        logger.info(f"Sending password change notification to {user.email}")
        
        # Try tenant-specific email first, fallback to Django's send_mail
        email_sent = False
        
        try:
            # Use tenant email if available
            email_sent = send_tenant_email(
                subject=subject,
                message=plain_message,
                recipient_list=recipient_list,
                request_or_org=user.organization,
                fail_silently=True,
                html_message=html_message
            )
            
            if email_sent:
                logger.info(f"Password change notification sent via tenant email to {user.email}")
            else:
                raise Exception("Tenant email failed")
                
        except Exception as tenant_error:
            logger.warning(f"Tenant email failed for {user.email}: {tenant_error}")
            
            # Fallback to Django's standard send_mail
            try:
                django_send_mail(
                    subject=subject,
                    message=plain_message,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=recipient_list,
                    fail_silently=False,
                    html_message=html_message
                )
                email_sent = True
                logger.info(f"Password change notification sent via Django email to {user.email}")
                
            except Exception as django_error:
                logger.error(f"Django email also failed for {user.email}: {django_error}")
                email_sent = False
        
        # Log the result
        if email_sent:
            logger.info(f"Password change notification successfully sent to {user.email}")
            if email_log:
                email_log.mark_sent()
        else:
            logger.error(f"Failed to send password change notification to {user.email}")
            if email_log:
                email_log.mark_failed("Email sending failed")
            
        return email_sent
        
    except Exception as e:
        logger.error(f"Unexpected error sending password change notification to {user.email}: {e}")
        if email_log:
            email_log.mark_failed(f"Unexpected error: {str(e)}")
        return False


def send_password_expiry_warning(user, days_until_expiry):
    """
    Send password expiry warning email to user.
    
    Args:
        user (CustomUser): The user whose password is expiring
        days_until_expiry (int): Number of days until password expires
        
    Returns:
        bool: True if email was sent successfully, False otherwise
    """
    if not user or not user.email:
        logger.warning(f"Password expiry warning skipped: invalid user or email")
        return False
    
    try:
        context = {
            'user': user,
            'days_until_expiry': days_until_expiry,
            'site_name': getattr(settings, 'SITE_NAME', 'Oreno GRC'),
            'site_domain': getattr(settings, 'SITE_DOMAIN', ''),
            'change_password_url': f"{getattr(settings, 'SITE_URL', '')}/users/password_change/",
        }
        
        # For now, use a simple message. In the future, create dedicated templates
        subject = _('Password Expires Soon - Action Required')
        message = f"""
Hello {user.get_full_name() or user.username},

Your password will expire in {days_until_expiry} days.

Please change your password before it expires to maintain access to your account.

Change your password: {context['change_password_url']}

If you have any questions, please contact your system administrator.

Best regards,
{context['site_name']} Team
        """.strip()
        
        # Send email using the same robust mechanism
        try:
            email_sent = send_tenant_email(
                subject=subject,
                message=message,
                recipient_list=[user.email],
                request_or_org=user.organization,
                fail_silently=True
            )
            
            if not email_sent:
                # Fallback to Django email
                django_send_mail(
                    subject=subject,
                    message=message,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[user.email],
                    fail_silently=False
                )
                email_sent = True
                
        except Exception as e:
            logger.error(f"Failed to send password expiry warning to {user.email}: {e}")
            return False
        
        logger.info(f"Password expiry warning sent to {user.email} ({days_until_expiry} days remaining)")
        return email_sent
        
    except Exception as e:
        logger.error(f"Unexpected error sending password expiry warning to {user.email}: {e}")
        return False


def send_security_alert(user, alert_type, details=None):
    """
    Send security alert email to user.
    
    This is a future-ready function for various security alerts:
    - Suspicious login attempts
    - Account lockouts
    - Password compromise notifications
    - etc.
    
    Args:
        user (CustomUser): The user to notify
        alert_type (str): Type of security alert
        details (dict, optional): Additional details for the alert
        
    Returns:
        bool: True if email was sent successfully, False otherwise
    """
    if not user or not user.email:
        logger.warning(f"Security alert skipped: invalid user or email")
        return False
    
    try:
        # Map alert types to subjects and messages
        alert_templates = {
            'suspicious_login': {
                'subject': _('Suspicious Login Attempt Detected'),
                'message': 'We detected a suspicious login attempt on your account.'
            },
            'account_locked': {
                'subject': _('Account Temporarily Locked'),
                'message': 'Your account has been temporarily locked due to multiple failed login attempts.'
            },
            'password_compromised': {
                'subject': _('Password Security Alert'),
                'message': 'Your password may have been compromised. Please change it immediately.'
            }
        }
        
        if alert_type not in alert_templates:
            logger.warning(f"Unknown security alert type: {alert_type}")
            return False
        
        template = alert_templates[alert_type]
        context = {
            'user': user,
            'alert_type': alert_type,
            'details': details or {},
            'site_name': getattr(settings, 'SITE_NAME', 'Oreno GRC'),
            'support_email': getattr(settings, 'SUPPORT_EMAIL', 'support@oreno.tech'),
        }
        
        subject = template['subject']
        message = f"""
Hello {user.get_full_name() or user.username},

{template['message']}

Details:
{details or 'No additional details available'}

If you did not perform this action, please contact your system administrator immediately.

Best regards,
{context['site_name']} Security Team
        """.strip()
        
        # Send email using the same robust mechanism
        try:
            email_sent = send_tenant_email(
                subject=subject,
                message=message,
                recipient_list=[user.email],
                request_or_org=user.organization,
                fail_silently=True
            )
            
            if not email_sent:
                # Fallback to Django email
                django_send_mail(
                    subject=subject,
                    message=message,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[user.email],
                    fail_silently=False
                )
                email_sent = True
                
        except Exception as e:
            logger.error(f"Failed to send security alert to {user.email}: {e}")
            return False
        
        logger.info(f"Security alert ({alert_type}) sent to {user.email}")
        return email_sent
        
    except Exception as e:
        logger.error(f"Unexpected error sending security alert to {user.email}: {e}")
        return False


def get_user_ip_address(request):
    """
    Extract user's IP address from request.
    Handles various proxy scenarios for future-ready implementation.
    
    Args:
        request (HttpRequest): Django request object
        
    Returns:
        str: IP address or 'Unknown'
    """
    if not request:
        return 'Unknown'
    
    # Check for forwarded IP (common in production with load balancers)
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        # Take the first IP in the chain
        ip = x_forwarded_for.split(',')[0].strip()
        return ip
    
    # Check for real IP header
    x_real_ip = request.META.get('HTTP_X_REAL_IP')
    if x_real_ip:
        return x_real_ip.strip()
    
    # Fallback to remote address
    return request.META.get('REMOTE_ADDR', 'Unknown')


def get_user_agent(request):
    """
    Extract user agent from request.
    
    Args:
        request (HttpRequest): Django request object
        
    Returns:
        str: User agent string or None
    """
    if not request:
        return None
    
    return request.META.get('HTTP_USER_AGENT')
