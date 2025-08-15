# GRC/oreno/apps/core/utils.py

import random
import string
import logging
from datetime import datetime
from django.core.mail import send_mail
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
