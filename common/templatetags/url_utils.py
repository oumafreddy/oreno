"""
Template tags for safe URL resolution that work across public and tenant schemas.
"""
from django import template
from django.urls import NoReverseMatch, reverse

register = template.Library()


@register.simple_tag(takes_context=True)
def safe_url(context, view_name, *args, **kwargs):
    """
    Safely resolve a URL by name. Returns None if the URL doesn't exist,
    allowing conditional rendering in templates.
    
    Usage:
        {% safe_url 'public-docs' as docs_url %}
        {% if docs_url %}
            <a href="{{ docs_url }}">Documentation</a>
        {% endif %}
    """
    try:
        return reverse(view_name, args=args, kwargs=kwargs)
    except NoReverseMatch:
        return None
