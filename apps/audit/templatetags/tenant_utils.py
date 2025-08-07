from django import template
from django_tenants.utils import get_public_schema_name

register = template.Library()

@register.simple_tag(takes_context=True)
def is_public_schema_safe(context, app):
    """
    A safer version of django_tenants' is_public_schema tag that handles None tenants.
    This fixes the 'NoneType' object has no attribute 'schema_name' error in admin templates.
    """
    # Check if request has a tenant attribute
    if not hasattr(context.request, 'tenant'):
        return True
    
    # Check if tenant is None
    if context.request.tenant is None:
        return True
    
    # Now safely check the schema_name
    return context.request.tenant.schema_name == get_public_schema_name()

@register.filter
def class_name(obj):
    """
    Returns the class name of an object.
    """
    return obj.__class__.__name__
