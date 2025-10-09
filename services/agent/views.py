from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import ValidationError

from .intent import IntentSerializer
from .executor import AgentExecutor

class AgentParseView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        prompt = request.data.get('prompt')
        active_app = request.data.get('active_app')
        if not prompt:
            raise ValidationError({'prompt': 'This field is required.'})
        # TODO: Call LLM mapping here. For now, return empty intent scaffold
        intent = request.data.get('intent') or {
            'action': 'create',
            'model': 'audit.AuditWorkplan',
            'fields': {}
        }
        ser = IntentSerializer(data=intent)
        ser.is_valid(raise_exception=True)
        return Response({
            'intent': ser.validated_data,
            'validation': {'valid': True, 'errors': {}},
            'preview': {'summary': f"Plan: {ser.validated_data}"}
        })

class AgentExecuteView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        intent = request.data.get('intent')
        confirm = request.data.get('confirm', False)
        if not intent:
            raise ValidationError({'intent': 'This field is required.'})
        if not confirm:
            raise ValidationError({'confirm': 'Confirmation required to execute.'})
        ser = IntentSerializer(data=intent)
        ser.is_valid(raise_exception=True)
        executor = AgentExecutor(request)
        result = executor.execute(ser.validated_data)
        return Response({'result': result})
