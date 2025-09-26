# GRC/oreno/apps/core/utils.py

import random
import string
import logging
from datetime import datetime
from django.core.mail import send_mail, get_connection, EmailMessage
from django.conf import settings
from django.utils.dateformat import format as django_date_format
from django.utils.translation import gettext_lazy as _

logger = logging.getLogger(__name__)

def generate_random_code(length=8):
    """
    Generate a random alphanumeric code of specified length.
    
    This is useful for generating OTP codes, temporary tokens, or unique customer codes.

    Args:
        length (int): The length of the generated code. Default is 8.

    Returns:
        str: A random alphanumeric string.
    """
    characters = string.ascii_uppercase + string.digits
    return ''.join(random.choices(characters, k=length))

def send_email_safe(subject, message, recipient_list, from_email=None, fail_silently=False):
    """
    Safely sends an email using Django's send_mail function.
    
    This utility wraps the email sending process with error handling and logging.
    
    Args:
        subject (str): Subject of the email.
        message (str): Body of the email.
        recipient_list (list): List of recipient email addresses.
        from_email (str, optional): Sender's email address. Defaults to settings.DEFAULT_FROM_EMAIL.
        fail_silently (bool): Whether to fail silently.

    Returns:
        bool: True if the email was sent successfully, False otherwise.
    """
    if from_email is None:
        from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@example.com')
    
    try:
        send_mail(subject, message, from_email, recipient_list, fail_silently=fail_silently)
        logger.info(f"Email sent to {', '.join(recipient_list)} with subject '{subject}'.")
        return True
    except Exception as e:
        logger.error(f"Error sending email: {e}")
        return False

def _resolve_org_from_request_or_org(request_or_org):
    try:
        # If a request was passed, prefer request.tenant then request.organization
        if hasattr(request_or_org, 'tenant'):
            return getattr(request_or_org, 'tenant', None) or getattr(request_or_org, 'organization', None)
        # If it looks like a model instance with schema_name or email domain, return as is
        return request_or_org
    except Exception:
        return None

def send_tenant_email(subject, message, recipient_list, request_or_org=None, from_email=None, fail_silently=False, html_message=None):
    """
    Send email using per-tenant SMTP settings if available, else fall back to global settings.

    Args:
        subject (str): Email subject
        message (str): Plain text body
        recipient_list (List[str]): Recipients
        request_or_org: Django request (with .tenant or .organization) or Organization instance
        from_email (str|None): Override From email; defaults to tenant or global DEFAULT_FROM_EMAIL
        fail_silently (bool): Whether to suppress errors
        html_message (str|None): Optional HTML body

    Returns:
        bool: True if at least one message was sent
    """
    org = _resolve_org_from_request_or_org(request_or_org)

    # Determine effective settings
    backend = getattr(settings, 'TENANT_EMAIL_BACKEND', settings.EMAIL_BACKEND) if hasattr(settings, 'TENANT_EMAIL_BACKEND') else getattr(settings, 'EMAIL_BACKEND', 'django.core.mail.backends.smtp.EmailBackend')
    host = getattr(settings, 'EMAIL_HOST', '')
    port = getattr(settings, 'EMAIL_PORT', 25)
    host_user = getattr(settings, 'EMAIL_HOST_USER', '')
    host_password = getattr(settings, 'EMAIL_HOST_PASSWORD', '')
    use_tls = getattr(settings, 'EMAIL_USE_TLS', True)
    use_ssl = getattr(settings, 'EMAIL_USE_SSL', False)
    timeout = getattr(settings, 'EMAIL_TIMEOUT', 30)
    default_from = getattr(settings, 'DEFAULT_FROM_EMAIL', 'info@oreno.tech')

    # If tenants.py provided tenant overrides, prefer them
    try:
        host = getattr(settings, 'TENANT_EMAIL_HOST', host)
        port = getattr(settings, 'TENANT_EMAIL_PORT', port)
        host_user = getattr(settings, 'TENANT_EMAIL_HOST_USER', host_user)
        host_password = getattr(settings, 'TENANT_EMAIL_HOST_PASSWORD', host_password)
        use_tls = getattr(settings, 'TENANT_EMAIL_USE_TLS', use_tls)
        default_from = getattr(settings, 'TENANT_DEFAULT_FROM_EMAIL', default_from)
    except Exception:
        pass

    # Allow organization-specific branding (from the model) if available
    try:
        if org and hasattr(org, 'email_from') and getattr(org, 'email_from'):
            default_from = org.email_from
    except Exception:
        pass

    from_addr = from_email or default_from

    try:
        connection = get_connection(
            backend=backend,
            host=host,
            port=port,
            username=host_user,
            password=host_password,
            use_tls=use_tls,
            use_ssl=use_ssl,
            timeout=timeout,
        )
        email = EmailMessage(subject, message, from_addr, recipient_list, connection=connection)
        if html_message:
            email.content_subtype = 'html'
            email.body = html_message
        sent = email.send(fail_silently=fail_silently)
        if sent:
            logger.info(f"Tenant email sent to {', '.join(recipient_list)} with subject '{subject}'.")
            return True
        return False
    except Exception as e:
        logger.error(f"Error sending tenant email: {e}")
        if fail_silently:
            return False
        raise

def format_date(date_obj, date_format='N j, Y'):
    """
    Formats a date object into a string using Django's date formatting conventions.
    
    Args:
        date_obj (datetime.date or datetime.datetime): The date to format.
        date_format (str): The format string as per Django's date format syntax.
                           Default is 'N j, Y' (e.g. "Mar 10, 2023").

    Returns:
        str: The formatted date string.
    """
    if not date_obj:
        return ""
    return django_date_format(date_obj, date_format)

def safe_cast(val, to_type, default=None):
    """
    Safely attempts to cast a value to a specified type.
    
    Args:
        val: The value to cast.
        to_type: The type to cast the value to (e.g., int, float).
        default: The default value to return if casting fails.

    Returns:
        The casted value if successful, else the default value.
    """
    try:
        return to_type(val)
    except (ValueError, TypeError):
        logger.warning(f"Failed to cast {val} to {to_type}. Returning default: {default}.")
        return default


def user_has_tenant_access(user, tenant):
    """
    Check if user has access to the specified tenant.
    
    Args:
        user: The authenticated user
        tenant: The tenant/organization being accessed
        
    Returns:
        bool: True if user has access, False otherwise
    """
    # Superusers can access all tenants (for admin purposes)
    if user.is_superuser:
        return True
    
    # Get user's assigned organization
    user_organization = getattr(user, 'organization', None)
    
    # If user has no organization assigned, they can't access any tenant
    if not user_organization:
        logger.warning(f"User {user.email} has no organization assigned")
        return False
    
    # Check if user's organization matches the tenant
    if hasattr(tenant, 'schema_name'):
        # For django-tenants, compare schema names
        has_access = user_organization.schema_name == tenant.schema_name
        if not has_access:
            logger.warning(
                f"User {user.email} (org: {user_organization.schema_name}) "
                f"attempted to access tenant {tenant.schema_name}"
            )
        return has_access
    else:
        # For direct organization comparison
        has_access = user_organization == tenant
        if not has_access:
            logger.warning(
                f"User {user.email} (org: {user_organization}) "
                f"attempted to access tenant {tenant}"
            )
        return has_access
