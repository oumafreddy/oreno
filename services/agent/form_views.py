"""
API Views for Form Agent
Provides endpoints for intelligent form pre-filling
"""
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import ValidationError, NotFound
from rest_framework import status
import logging

from .form_agent import FormAgent
from .schema_index import get_schema_index

logger = logging.getLogger('services.agent.form_views')


class PrefillFormView(APIView):
    """
    Pre-fill form fields intelligently based on user input
    POST /api/agent/prefill/
    
    Body:
    {
        "model": "audit.AuditWorkplan",
        "fields": {
            "title": "Annual Audit Plan",
            "year": 2025
        },
        "context": {
            "fiscal_year": 2025
        }
    }
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        """Pre-fill form fields"""
        model_path = request.data.get('model')
        user_fields = request.data.get('fields', {})
        context = request.data.get('context', {})
        
        if not model_path:
            raise ValidationError({'model': 'Model path is required'})
        
        # Check if model exists
        schema_index = get_schema_index()
        schema = schema_index.get_model_schema(model_path)
        if not schema:
            raise NotFound(f"Model '{model_path}' not found")
        
        # Initialize form agent
        agent = FormAgent(request.user)
        
        # Pre-fill form
        try:
            result = agent.prefill_form(model_path, user_fields, context)
            
            return Response({
                'model': model_path,
                'prefilled_fields': result['fields'],
                'suggestions': result['suggestions'],
                'warnings': result['warnings'],
                'errors': result['errors'],
                'missing_required': result['missing_required'],
                'ready_to_save': result['ready_to_save'],
                'security_checks': result['security_checks']
            })
        
        except Exception as e:
            logger.error(f"Error pre-filling form for {model_path}: {e}")
            return Response(
                {'detail': f'Error pre-filling form: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class SuggestFieldView(APIView):
    """
    Get suggestions for a specific field
    GET /api/agent/suggest/{model_path}/{field_name}/?q=query
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request, model_path, field_name):
        """Get field suggestions"""
        query = request.query_params.get('q', '')
        
        schema_index = get_schema_index()
        schema = schema_index.get_model_schema(model_path)
        if not schema:
            raise NotFound(f"Model '{model_path}' not found")
        
        field_info = schema_index.get_field_info(model_path, field_name)
        if not field_info:
            raise NotFound(f"Field '{field_name}' not found in model '{model_path}'")
        
        # If it's a ForeignKey, suggest related objects
        if field_info.get('type') == 'ForeignKey':
            agent = FormAgent(request.user)
            related_model = field_info.get('related_model')
            if related_model:
                suggestions = agent._suggest_related_objects(related_model, field_name, {})
                
                # Filter by query if provided
                if query and suggestions:
                    query_lower = query.lower()
                    suggestions = [
                        s for s in suggestions
                        if query_lower in s.get('name', '').lower() or 
                           query_lower in str(s.get('code', '')).lower()
                    ]
                
                return Response({
                    'field': field_name,
                    'type': 'ForeignKey',
                    'related_model': related_model,
                    'suggestions': suggestions or []
                })
        
        # If it's a choice field, return choices
        if field_info.get('has_choices'):
            choices = field_info.get('choices', [])
            
            # Filter by query if provided
            if query:
                query_lower = query.lower()
                choices = [
                    c for c in choices
                    if query_lower in c.get('label', '').lower() or 
                       query_lower in str(c.get('value', '')).lower()
                ]
            
            return Response({
                'field': field_name,
                'type': 'ChoiceField',
                'choices': choices
            })
        
        return Response({
            'field': field_name,
            'type': field_info.get('type'),
            'suggestions': []
        })

