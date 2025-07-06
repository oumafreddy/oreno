#!/usr/bin/env python
"""
Quick test script to verify AI assistant is working.
Run this from the oreno directory with: python test_ai_working.py
"""
import os
import sys
import django

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from services.ai.ai_service import ai_assistant_answer
from services.ai.ollama_adapter import check_ollama_status

def test_ai_assistant():
    """Test the AI assistant with a simple question"""
    print("🤖 Testing AI Assistant...")
    
    # Check if Ollama is running
    print("📡 Checking Ollama status...")
    if not check_ollama_status():
        print("❌ Ollama is not running!")
        print("   Please start Ollama with: ollama serve")
        return False
    
    print("✅ Ollama is running")
    
    # Test with a simple question
    test_question = "What is GRC?"
    print(f"\n🔍 Testing with question: '{test_question}'")
    
    try:
        response = ai_assistant_answer(test_question, "test_user", "test_org")
        print(f"✅ AI Response: {response}")
        return True
    except Exception as e:
        print(f"❌ AI Error: {e}")
        return False

if __name__ == "__main__":
    success = test_ai_assistant()
    if success:
        print("\n🎉 AI Assistant is working correctly!")
    else:
        print("\n⚠️  AI Assistant needs attention. Check the errors above.")
        sys.exit(1) 