from django.shortcuts import render
from django.utils.translation import gettext as _

def bad_request(request, exception=None):
    """400 error handler"""
    context = {
        'title': _('Bad Request (400)'),
        'message': _('The request could not be understood by the server.'),
        'exception': exception,
    }
    return render(request, 'core/error.html', context, status=400)

def permission_denied(request, exception=None):
    """403 error handler"""
    context = {
        'title': _('Permission Denied (403)'),
        'message': _('You do not have permission to access this resource.'),
        'exception': exception,
    }
    return render(request, 'core/error.html', context, status=403)

def page_not_found(request, exception=None):
    """404 error handler"""
    context = {
        'title': _('Page Not Found (404)'),
        'message': _('The requested page could not be found.'),
        'exception': exception,
    }
    return render(request, 'core/error.html', context, status=404)

def server_error(request):
    """500 error handler"""
    context = {
        'title': _('Server Error (500)'),
        'message': _('An internal server error occurred.'),
    }
    return render(request, 'core/error.html', context, status=500) 