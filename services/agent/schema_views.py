"""
API Views for Schema Intelligence
Provides endpoints to access comprehensive schema information
"""
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import NotFound, ValidationError
from rest_framework import status
import logging

from .schema_index import get_schema_index, rebuild_schema_index

logger = logging.getLogger('services.agent.schema_views')


class SchemaListView(APIView):
    """
    List all available models in the schema index
    GET /api/agent/schema/
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """List all models, optionally filtered by app"""
        app_name = request.query_params.get('app', None)
        schema_index = get_schema_index()
        
        models = schema_index.list_models(app_name=app_name)
        
        return Response({
            'models': models,
            'count': len(models),
            'apps': list(set([m.split('.')[0] for m in models]))
        })


class SchemaDetailView(APIView):
    """
    Get detailed schema for a specific model
    GET /api/agent/schema/{model_path}/
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request, model_path):
        """Get complete schema for a model"""
        schema_index = get_schema_index()
        schema = schema_index.get_model_schema(model_path)
        
        if not schema:
            raise NotFound(f"Model '{model_path}' not found in schema index")
        
        return Response(schema)


class FieldDetailView(APIView):
    """
    Get detailed information about a specific field
    GET /api/agent/schema/{model_path}/fields/{field_name}/
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request, model_path, field_name):
        """Get detailed info about a field"""
        schema_index = get_schema_index()
        field_info = schema_index.get_field_info(model_path, field_name)
        
        if not field_info:
            raise NotFound(f"Field '{field_name}' not found in model '{model_path}'")
        
        return Response(field_info)


class SerializerInfoView(APIView):
    """
    Get serializer information for a model
    GET /api/agent/schema/{model_path}/serializer/
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request, model_path):
        """Get serializer info for a model"""
        schema_index = get_schema_index()
        serializer_info = schema_index.get_serializer_for_model(model_path)
        
        if not serializer_info:
            raise NotFound(f"Serializer not found for model '{model_path}'")
        
        return Response(serializer_info)


class FormInfoView(APIView):
    """
    Get form information for a model
    GET /api/agent/schema/{model_path}/form/
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request, model_path):
        """Get form info for a model"""
        schema_index = get_schema_index()
        form_info = schema_index.get_form_for_model(model_path)
        
        if not form_info:
            raise NotFound(f"Form not found for model '{model_path}'")
        
        return Response(form_info)


class SchemaRebuildView(APIView):
    """
    Rebuild the schema index (admin only)
    POST /api/agent/schema/rebuild/
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        """Rebuild the schema index"""
        # Check if user has permission (you can add custom permission check here)
        if not request.user.is_staff:
            return Response(
                {'detail': 'Only staff users can rebuild the schema index'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        try:
            schema_index = rebuild_schema_index()
            return Response({
                'status': 'success',
                'models_indexed': len(schema_index.models),
                'serializers_indexed': len(schema_index.serializers),
                'forms_indexed': len(schema_index.forms),
            })
        except Exception as e:
            logger.error(f"Error rebuilding schema index: {e}")
            return Response(
                {'detail': f'Error rebuilding schema index: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class SchemaSearchView(APIView):
    """
    Search for models/fields by name or type
    GET /api/agent/schema/search/?q=query&type=model|field
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """Search schema index"""
        query = request.query_params.get('q', '').lower()
        search_type = request.query_params.get('type', 'model')  # model or field
        
        if not query:
            raise ValidationError({'q': 'Query parameter is required'})
        
        schema_index = get_schema_index()
        results = []
        
        if search_type == 'model':
            # Search model names
            for model_path, schema in schema_index.models.items():
                if query in model_path.lower() or query in schema.get('model', '').lower():
                    results.append({
                        'model_path': model_path,
                        'model': schema.get('model'),
                        'app': schema.get('app'),
                        'verbose_name': schema.get('meta', {}).get('verbose_name'),
                    })
        elif search_type == 'field':
            # Search field names
            for model_path, schema in schema_index.models.items():
                for field_name, field_info in schema.get('fields', {}).items():
                    if (query in field_name.lower() or 
                        query in field_info.get('verbose_name', '').lower() or
                        query in (field_info.get('help_text') or '').lower()):
                        results.append({
                            'model_path': model_path,
                            'model': schema.get('model'),
                            'field_name': field_name,
                            'field_type': field_info.get('type'),
                            'verbose_name': field_info.get('verbose_name'),
                        })
        
        return Response({
            'query': query,
            'type': search_type,
            'results': results,
            'count': len(results)
        })

