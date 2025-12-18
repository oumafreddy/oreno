"""
Test script for AI Agent functionality
Tests intent parsing and execution capabilities
"""
import os
import sys
import django

# Setup Django
sys.path.insert(0, os.path.dirname(__file__))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.tenants')
django.setup()

from django.contrib.auth import get_user_model
from organizations.models import Organization
from services.agent.views import AgentParseView, AgentExecuteView
from rest_framework.test import APIRequestFactory
from rest_framework import status
import json

def test_agent_parse(prompt: str, user, org):
    """Test intent parsing"""
    print(f"\n{'='*60}")
    print(f"Testing Intent Parsing")
    print(f"{'='*60}")
    print(f"Prompt: {prompt}")
    print(f"User: {user.username}")
    print(f"Organization: {org.name}")
    
    factory = APIRequestFactory()
    view = AgentParseView.as_view()
    
    request = factory.post('/api/agent/parse/', {
        'prompt': prompt,
        'active_app': 'audit'
    }, format='json')
    request.user = user
    
    try:
        response = view(request)
        print(f"\nStatus Code: {response.status_code}")
        
        if response.status_code == 200:
            data = json.loads(response.content)
            intent = data.get('intent', {})
            print(f"\n[SUCCESS] Parsed Intent:")
            print(f"   Action: {intent.get('action')}")
            print(f"   Model: {intent.get('model')}")
            print(f"   Fields: {intent.get('fields')}")
            print(f"   Confidence: {intent.get('confidence')}")
            print(f"\nPreview: {data.get('preview', {}).get('summary')}")
            return intent
        else:
            print(f"\n[ERROR] Error: {response.data}")
            return None
    except Exception as e:
        print(f"\n[ERROR] Exception: {e}")
        import traceback
        traceback.print_exc()
        return None

def test_agent_execute(intent: dict, user, org, preview=True):
    """Test intent execution"""
        if not intent or intent.get('action') == 'unknown':
            print("\n[WARNING] Skipping execution - invalid intent")
            return None
    
    print(f"\n{'='*60}")
    print(f"Testing Intent Execution (Preview Mode)")
    print(f"{'='*60}")
    
    factory = APIRequestFactory()
    view = AgentExecuteView.as_view()
    
    request = factory.post('/api/agent/execute/', {
        'intent': intent,
        'preview': preview,
        'confirm': False
    }, format='json')
    request.user = user
    
    # Set tenant context
    from django_tenants.utils import tenant_context
    org.schema_name = org.schema_name if hasattr(org, 'schema_name') else 'public'
    
    try:
        with tenant_context(org):
            response = view(request)
            print(f"\nStatus Code: {response.status_code}")
            
            if response.status_code == 200:
                data = json.loads(response.content)
                print(f"\n[SUCCESS] Execution Result:")
                print(json.dumps(data, indent=2))
                return data
            else:
                print(f"\n[ERROR] Error: {response.data}")
                return None
    except Exception as e:
        print(f"\n[ERROR] Exception: {e}")
        import traceback
        traceback.print_exc()
        return None

def main():
    """Run agent tests"""
    print("\n" + "="*60)
    print("AI Agent Test Suite")
    print("="*60)
    
    # Get test user and organization
    User = get_user_model()
    try:
        user = User.objects.filter(is_superuser=True).first()
        if not user:
            print("[ERROR] No superuser found. Please create one first.")
            return
        
        org = getattr(user, 'organization', None)
        if not org:
            orgs = Organization.objects.all()
            if orgs.exists():
                org = orgs.first()
            else:
                print("[ERROR] No organization found. Please create one first.")
                return
        
        print(f"\nUsing User: {user.username}")
        print(f"Using Organization: {org.name}")
        
        # Test cases
        test_cases = [
            "Create a new audit workplan for 2025",
            "Show me all open issues",
            "What engagements do I have?",
            "Create an engagement for Q1 2025 audit",
            "Update issue with ID 1 to set status as resolved",
        ]
        
        results = []
        for prompt in test_cases:
            intent = test_agent_parse(prompt, user, org)
            if intent:
                result = test_agent_execute(intent, user, org, preview=True)
                results.append({'prompt': prompt, 'intent': intent, 'result': result})
            
            print("\n" + "-"*60)
        
        # Summary
        print(f"\n{'='*60}")
        print("Test Summary")
        print(f"{'='*60}")
        print(f"Total tests: {len(test_cases)}")
        successful = sum(1 for r in results if r.get('intent') and r['intent'].get('action') != 'unknown')
        print(f"Successful parses: {successful}/{len(test_cases)}")
        
    except Exception as e:
        print(f"\n[ERROR] Setup Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    main()

