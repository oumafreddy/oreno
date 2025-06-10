from django.shortcuts import get_object_or_404
from .models import Issue

def get_issue_from_pk(issue_pk, organization=None):
    """
    Safely get an Issue instance from issue_pk, with optional organization filtering.
    Returns None if issue_pk is None or empty.
    """
    if not issue_pk:
        return None
        
    filters = {'pk': issue_pk}
    if organization:
        filters['organization'] = organization
        
    return get_object_or_404(Issue, **filters)

def get_issue_pk_from_request(request):
    """
    Extract issue_pk from various request sources (GET, POST, kwargs).
    Returns None if not found.
    """
    return (
        request.GET.get('issue_pk') or 
        request.POST.get('issue_pk') or 
        request.resolver_match.kwargs.get('issue_pk')
    ) 