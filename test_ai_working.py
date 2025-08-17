#!/usr/bin/env python3
"""
Simple test script to verify AI functionality with organization data
"""
import os
import sys
import django

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.tenants')
django.setup()

from services.ai.ai_service import ai_assistant_answer, find_faq_answer, get_user_context, OrganizationDataProvider

def test_ai_functionality():
    """Test basic AI functionality with organization data"""
    print("🧪 Testing AI Functionality with Organization Data...")
    
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
        
        # Test organization data provider
        print("\n3. Testing Organization Data Provider...")
        data_provider = OrganizationDataProvider(user, org)
        org_summary = data_provider.get_organization_summary()
        print(f"✅ Organization summary created with {len(org_summary)} data categories")
        
        # Test AI response with data
        print("\n4. Testing AI response with organization data...")
        response = ai_assistant_answer("what is your role?", user, org)
        print(f"✅ AI Response: {response}")
        
        # Test data-aware questions
        print("\n5. Testing data-aware questions...")
        data_questions = [
            "How many workplans do I have?",
            "What are my current risks?",
            "Show me my compliance status",
            "What contracts are expiring soon?"
        ]
        
        for question in data_questions:
            try:
                response = ai_assistant_answer(question, user, org)
                print(f"✅ Data question '{question}': {response[:150]}...")
            except Exception as e:
                print(f"❌ Error with data question '{question}': {e}")
        
    except Exception as e:
        print(f"❌ Error testing AI: {e}")
    
    print("\n🎉 AI functionality test completed!")

if __name__ == "__main__":
    test_ai_functionality() 