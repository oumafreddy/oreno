"""
Utility script to test the Ollama integration.
This script helps verify that the Ollama setup is working correctly.

Usage:
    python test_ollama.py "Your test question here"
"""
import os
import sys
import django

# Set up Django environment
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from services.ai.ollama_adapter import ask_ollama
from services.ai.llm_adapter import ask_llm

def test_ollama_direct(question):
    """Test Ollama directly using the ask_ollama function"""
    print("\n=== Testing Ollama directly ===")
    print(f"Question: {question}")
    response = ask_ollama(question, "test_user", "test_org")
    print(f"Ollama Response: {response}")
    return response

def test_llm_adapter(question):
    """Test using the main LLM adapter which might use Ollama or fallback to OpenAI"""
    print("\n=== Testing LLM Adapter (might use Ollama or OpenAI) ===")
    print(f"Question: {question}")
    response = ask_llm(question, "test_user", "test_org")
    print(f"LLM Adapter Response: {response}")
    return response

def check_ollama_running():
    """Check if Ollama is running by importing requests and checking the server"""
    import requests
    from services.ai.ollama_config import OLLAMA_BASE_URL
    
    try:
        response = requests.get(f"{OLLAMA_BASE_URL}/api/tags")
        if response.status_code == 200:
            models = response.json().get("models", [])
            print("\n=== Ollama Status: RUNNING ===")
            print(f"Available models: {[model['name'] for model in models]}")
            return True
        else:
            print("\n=== Ollama Status: NOT RESPONDING CORRECTLY ===")
            print(f"Status code: {response.status_code}")
            return False
    except Exception as e:
        print("\n=== Ollama Status: NOT RUNNING ===")
        print(f"Error: {e}")
        return False

if __name__ == "__main__":
    # Check if Ollama is running
    check_ollama_running()
    
    # Get the question from command line arguments or use a default
    question = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else "What is GRC and how can it help my organization?"
    
    # Test with direct Ollama call
    test_ollama_direct(question)
    
    # Test with LLM adapter (might use Ollama or OpenAI)
    test_llm_adapter(question)
