from django import template
import bleach

register = template.Library()

ALLOWED_TAGS = [
    'b', 'i', 'u', 'br', 'p', 'ul', 'ol', 'li', 'a', 'strong', 'em'
]
ALLOWED_ATTRIBUTES = {
    'a': ['href', 'title', 'target'],
}

@register.filter(name='limited_html')
def limited_html(value):
    """
    Safely render a limited subset of HTML tags and attributes.
    Usage: {{ value|limited_html|safe }}
    """
    if not value:
        return ''
    return bleach.clean(
        value,
        tags=ALLOWED_TAGS,
        attributes=ALLOWED_ATTRIBUTES,
        strip=True
    )

# If bleach is not installed, add it to requirements.txt: bleach>=6.0.0 