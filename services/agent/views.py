from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import ValidationError
from rest_framework import status
import json
import logging
from typing import cast, Dict, Any  # type: ignore[reportMissingImports]

from .intent import IntentSerializer
from .executor import AgentExecutor
from services.ai.ai_service import ai_assistant_answer
from services.agent.schema_index import get_schema_index

logger = logging.getLogger('services.agent.views')

class AgentParseView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        prompt = request.data.get('prompt')
        active_app = request.data.get('active_app')
        if not prompt:
            raise ValidationError({'prompt': 'This field is required.'})
        
        org = getattr(request.user, 'organization', None)
        if not org:
            raise ValidationError({'detail': 'Organization context required'})
        
        # Get available models from schema index
        schema_index = get_schema_index()
        available_models = schema_index.list_models()
        model_list = ', '.join([f"'{m}'" for m in available_models])
        
        # Build system prompt for intent parsing
        system_prompt = (
            "You are an intent parser for a GRC (Governance, Risk, Compliance) system. "
            "Your task is to parse user requests and return a JSON object matching this exact schema:\n"
            "{\n"
            "  'action': 'create' | 'update' | 'delete' | 'read' | 'generate_report',\n"
            "  'model': one of the available models: " + model_list + ",\n"
            "  'fields': { 'field_name': 'value', ... } (only include fields mentioned in the request),\n"
            "  'confidence': float between 0.0 and 1.0\n"
            "}\n\n"
            "Rules:\n"
            "- If the user wants to create something, use action='create'\n"
            "- If the user wants to modify something, use action='update'\n"
            "- If the user wants to delete something, use action='delete'\n"
            "- If the user wants to view/query something, use action='read'\n"
            "- Extract field values from the user's request\n"
            "- Set confidence based on how certain you are (0.0 = uncertain, 1.0 = very certain)\n"
            "- If you cannot parse the request, return: {'action': 'unknown', 'confidence': 0.0}\n"
            "- Return ONLY valid JSON, no other text\n"
        )
        
        user_prompt = f"{prompt}\n\nRespond with a single JSON object only, no explanations."
        
        try:
            # Call LLM to parse intent
            llm_response_raw = ai_assistant_answer(
                user_prompt,
                request.user,
                org,
                system_prompt=system_prompt,
                return_meta=False
            )
            
            # Type assertion: return_meta=False ensures str return type
            llm_response_str: str = cast(str, llm_response_raw) if isinstance(llm_response_raw, str) else str(llm_response_raw)
            
            # Clean response - remove markdown code blocks if present
            llm_response = llm_response_str.strip()
            if llm_response.startswith('```json'):
                llm_response = llm_response[7:]
            if llm_response.startswith('```'):
                llm_response = llm_response[3:]
            if llm_response.endswith('```'):
                llm_response = llm_response[:-3]
            llm_response = llm_response.strip()
            
            # Parse JSON
            try:
                parsed = json.loads(llm_response)
            except json.JSONDecodeError as e:
                logger.warning(f"Failed to parse LLM response as JSON: {llm_response[:200]}")
                # Fallback to safe response
                parsed = {'action': 'unknown', 'confidence': 0.0, 'model': None, 'fields': {}}
            
            # Validate via serializer
            serializer = IntentSerializer(data=parsed)
            if not serializer.is_valid():
                logger.warning(f"Intent validation failed: {serializer.errors}")
                # Return error with details
                return Response({
                    'error': 'Could not map to valid intent',
                    'details': serializer.errors,
                    'raw_llm_response': llm_response[:500],  # First 500 chars for debugging
                    'intent': parsed
                }, status=status.HTTP_400_BAD_REQUEST)
            
            validated_intent_raw = serializer.validated_data
            
            # Type assertion: validated_data is guaranteed to be a dict after is_valid()
            validated_intent: Dict[str, Any] = cast(Dict[str, Any], validated_intent_raw)
            
            # Check confidence threshold (optional - you can adjust this)
            confidence = validated_intent.get('confidence', 0.0)
            if confidence < 0.3:
                logger.warning(f"Low confidence intent: {confidence}")

            # Successful parse/validation response
            return Response({
                'intent': validated_intent,
                'validation': {'valid': True, 'errors': {}},
                'preview': {
                    'summary': (
                        f"Action: {validated_intent.get('action')}, "
                        f"Model: {validated_intent.get('model')}, "
                        f"Confidence: {confidence}"
                    )
                }
            })
            
        except Exception as e:
            logger.error(f"Error in intent parsing: {e}")
            # Fallback to safe response
            fallback_intent = {
                'action': 'unknown',
                'confidence': 0.0,
                'model': None,
                'fields': {}
            }
            serializer = IntentSerializer(data=fallback_intent)
            serializer.is_valid(raise_exception=True)
            return Response({
                'intent': serializer.validated_data,
                'validation': {'valid': False, 'errors': {'parsing_error': str(e)}},
                'preview': {'summary': 'Could not parse intent'}
            }, status=status.HTTP_200_OK)  # Return 200 but with low confidence

class AgentExecuteView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        intent = request.data.get('intent')
        if not intent:
            raise ValidationError({'intent': 'This field is required.'})
        ser = IntentSerializer(data=intent)
        ser.is_valid(raise_exception=True)
        validated_raw = ser.validated_data

        # Type assertion: validated_data is guaranteed to be a dict after is_valid()
        validated: Dict[str, Any] = cast(Dict[str, Any], validated_raw)

        # Preview mode: return planned changes without executing
        preview = validated.get('preview', False)
        confirm = request.data.get('confirm', False)
        action = validated.get('action')
        is_mutation = action in ['create', 'update', 'delete']

        if is_mutation and not (confirm or preview):
            raise ValidationError({'confirm': 'Confirmation required to execute.'})

        executor = AgentExecutor(request)
        result = executor.execute(validated, preview=preview)
        return Response({'result': result, 'preview': preview})
