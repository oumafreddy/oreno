"""
Utility functions for the audit app.
"""

def is_htmx_request(request):
    """
    Safely check if the request is an HTMX request.
    Handles possible attribute errors.
    """
    return request.headers.get('HX-Request') == 'true'
