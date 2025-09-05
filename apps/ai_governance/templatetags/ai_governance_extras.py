"""
Custom template filters and tags for AI Governance app.
"""

from django import template

register = template.Library()


@register.filter
def dict_get(dictionary, key):
    """
    Get a value from a dictionary using a key.
    Usage: {{ dictionary|dict_get:key }}
    """
    if isinstance(dictionary, dict):
        return dictionary.get(key, 0)
    return 0


@register.filter
def dict_keys(dictionary):
    """
    Get all keys from a dictionary.
    Usage: {{ dictionary|dict_keys }}
    """
    if isinstance(dictionary, dict):
        return dictionary.keys()
    return []


@register.filter
def dict_values(dictionary):
    """
    Get all values from a dictionary.
    Usage: {{ dictionary|dict_values }}
    """
    if isinstance(dictionary, dict):
        return dictionary.values()
    return []


@register.filter
def dict_items(dictionary):
    """
    Get all key-value pairs from a dictionary.
    Usage: {{ dictionary|dict_items }}
    """
    if isinstance(dictionary, dict):
        return dictionary.items()
    return []


@register.filter
def calculate_average(values):
    """
    Calculate the average of a list of values.
    Usage: {{ values|calculate_average }}
    """
    if not values:
        return 0
    
    try:
        numeric_values = [float(v) for v in values if v is not None]
        if numeric_values:
            return round(sum(numeric_values) / len(numeric_values))
    except (ValueError, TypeError):
        pass
    
    return 0


@register.filter
def format_percentage(value, decimals=0):
    """
    Format a number as a percentage.
    Usage: {{ value|format_percentage:1 }}
    """
    try:
        float_value = float(value)
        return f"{float_value:.{decimals}f}%"
    except (ValueError, TypeError):
        return "0%"


@register.filter
def get_item(dictionary, key):
    """
    Alternative to dict_get for better readability.
    Usage: {{ dictionary|get_item:key }}
    """
    return dict_get(dictionary, key)
