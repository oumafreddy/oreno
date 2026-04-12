"""
safe_filters.py — Template filter for sanitising CKEditor/rich-text HTML before rendering.

Usage in templates:
    {% load safe_filters %}
    {{ object.rich_text_field|safe_html }}

Replace |safe on any field whose value originates from user input (CKEditor, textarea, etc.).
Keep |safe only for values that are entirely application-generated (form widgets, reverse(), etc.).
"""

import bleach
from django import template
from django.utils.safestring import mark_safe

register = template.Library()

# HTML tags allowed from CKEditor 5 toolbar (conservative whitelist)
_ALLOWED_TAGS = [
    "a", "abbr", "b", "blockquote", "br", "caption", "cite", "code",
    "col", "colgroup", "dd", "div", "dl", "dt", "em", "h1", "h2", "h3",
    "h4", "h5", "h6", "hr", "i", "img", "li", "ol", "p", "pre", "s",
    "small", "span", "strong", "sub", "sup", "table", "tbody", "td",
    "tfoot", "th", "thead", "tr", "u", "ul",
]

# Attributes allowed per tag; callable form lets us enforce rel on <a>
def _allowed_attributes(tag, name, value):
    if tag == "a":
        return name in {"href", "title", "target", "rel"}
    if tag == "img":
        return name in {"src", "alt", "width", "height"}
    if tag in {"td", "th"}:
        return name in {"colspan", "rowspan", "scope"}
    if name in {"class", "id"}:
        return True
    return False


@register.filter(name="safe_html", is_safe=True)
def safe_html(value):
    """
    Sanitise HTML from a rich-text (CKEditor) field before rendering.
    Strips disallowed tags and attributes; forces rel='noopener noreferrer'
    on every <a> tag to prevent tab-napping via target='_blank'.
    """
    if not value:
        return value

    cleaned = bleach.clean(
        str(value),
        tags=_ALLOWED_TAGS,
        attributes=_allowed_attributes,
        strip=True,           # strip (not escape) disallowed tags
        strip_comments=True,  # remove HTML comments that could hide payloads
    )

    return mark_safe(cleaned)
