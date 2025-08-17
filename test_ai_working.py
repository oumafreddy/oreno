#!/usr/bin/env python3
"""
Simple test script to verify AI functionality
"""
import os
import sys
import django

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.tenants')
django.setup()

from services.ai.ai_service import ai_assistant_answer, find_faq_answer, get_user_context

def test_ai_functionality():
    """Test basic AI functionality"""
    print("🧪 Testing AI Functionality...")
    
    # Test FAQ matching
    print("\n1. Testing FAQ matching...")
    test_questions = [
        "what is your role?",
        "how do i use the legal app?",
        "what is grc?",
        "how do i create a workplan?",
    ]
    
    for question in test_questions:
        answer = find_faq_answer(question)
        if answer:
            print(f"✅ FAQ match for '{question}': {answer[:100]}...")
        else:
            print(f"❌ No FAQ match for '{question}'")
    
    # Test user context creation
    print("\n2. Testing user context creation...")
    try:
        # Mock user and org for testing
        class MockUser:
            def __init__(self):
                self.id = 1
                self.username = "test_user"
                self.is_authenticated = True
                self.role = "user"
            
            def get_all_permissions(self):
                return ["test.permission"]
        
        class MockOrg:
            def __init__(self):
                self.id = 1
                self.name = "Test Organization"
        
        user = MockUser()
        org = MockOrg()
        
        context = get_user_context(user, org)
        print(f"✅ User context created: {context['organization_name']}")
        
        # Test AI response
        print("\n3. Testing AI response...")
        response = ai_assistant_answer("what is your role?", user, org)
        print(f"✅ AI Response: {response}")
        
    except Exception as e:
        print(f"❌ Error testing AI: {e}")
    
    print("\n🎉 AI functionality test completed!")

if __name__ == "__main__":
    test_ai_functionality() 