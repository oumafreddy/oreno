from django.shortcuts import render
from django.utils.translation import gettext as _
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from services.ai.ai_service import ai_assistant_answer

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

class AIAssistantAPIView(APIView):
    # Allow both authenticated and unauthenticated users
    permission_classes = []
    
    def post(self, request, *args, **kwargs):
        question = request.data.get('question', '').strip()
        if not question:
            return Response({'answer': 'Please enter a question.'}, status=200)
        
        user = request.user if request.user.is_authenticated else None
        org = getattr(request, 'tenant', None) or getattr(request, 'organization', None)
        try:
            answer = ai_assistant_answer(question, user, org)
            if not answer:
                answer = 'Sorry, I could not find an answer to your question.'
            return Response({'answer': answer})
        except Exception as e:
            import logging
            logging.getLogger('services.ai.ai_service').error(f"AI Assistant error: {e}")
            return Response({'answer': 'Sorry, there was a problem processing your request. Please try again later.'}, status=200)