from rest_framework import serializers
from .models import DocumentRequest, Document

class DocumentRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = DocumentRequest
        fields = [
            'id', 'request_name', 'status', 'file', 'due_date', 'date_of_request',
            'request_owner', 'requestee', 'requestee_email', 'requestee_identifier',
            'remarks', 'organization', 'upload_token', 'token_expiry'
        ]
        read_only_fields = ('upload_token', 'token_expiry', 'organization')

class DocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Document
        fields = [
            'id', 'document_request', 'file', 'uploaded_at', 'uploaded_by', 'organization'
        ]
        read_only_fields = ('uploaded_at', 'organization') 