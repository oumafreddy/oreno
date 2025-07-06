#!/usr/bin/env python3
"""
Test script for Ollama integration
Usage: python test_ollama.py "Your question here"
"""

import sys
import requests
import json
from ollama_adapter import ask_ollama, check_ollama_status

def test_ollama_direct_api(question: str):
    """Test direct Ollama API call"""
    print(f"Question: {question}")
    
    # Use the correct model that the user has installed
    model = "llama3:8b"
    
    payload = {
        "model": model,
        "messages": [
            {"role": "user", "content": question}
        ],
        "stream": False
    }
    
    try:
        response = requests.post(
            "http://localhost:11434/api/chat",
            headers={"Content-Type": "application/json"},
            data=json.dumps(payload),
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            answer = result.get("message", {}).get("content", "").strip()
            print(f"✅ Ollama Direct Response: {answer}")
            return True
        else:
            print(f"❌ Ollama API error: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Ollama Error: {e}")
        return False

def test_ai_service(question: str):
    """Test the full AI service"""
    print(f"Question: {question}")
    
    try:
        # Mock user and org for testing
        user = "test_user"
        org = "test_org"
        
        response = ask_ollama(question, user, org)
        print(f"✅ AI Service Response: {response}")
        return True
        
    except Exception as e:
        print(f"❌ AI Service Error: {e}")
        return False

def main():
    if len(sys.argv) < 2:
        print("Usage: python test_ollama.py 'Your question here'")
        sys.exit(1)
    
    question = sys.argv[1]
    
    print("=== Testing Ollama Connection ===")
    
    # Check if Ollama is running
    if check_ollama_status():
        print("✅ Ollama is running and accessible")
    
        # Get available models
        try:
            response = requests.get("http://localhost:11434/api/tags", timeout=5)
            if response.status_code == 200:
                models = response.json().get("models", [])
                model_names = [model.get("name", "") for model in models]
                print(f"📋 Available models: {model_names}")
            else:
                print("⚠️  Could not retrieve model list")
        except Exception as e:
            print(f"⚠️  Error getting model list: {e}")
    else:
        print("❌ Ollama is not running")
        print("Please start Ollama with: ollama serve")
        sys.exit(1)
    
    print(f"\n🔍 Testing with question: '{question}'")
    
    print("\n=== Testing Ollama Direct API ===")
    direct_success = test_ollama_direct_api(question)
    
    print("\n=== Testing Full AI Service ===")
    service_success = test_ai_service(question)
    
    print("\n=== Test Summary ===")
    print(f"Ollama Direct: {'✅ PASS' if direct_success else '❌ FAIL'}")
    print(f"AI Service: {'✅ PASS' if service_success else '❌ FAIL'}")
    
    if not direct_success or not service_success:
        print("\n⚠️  Some tests failed. Check the error messages above.")
        sys.exit(1)
    else:
        print("\n🎉 All tests passed!")

if __name__ == "__main__":
    main()
