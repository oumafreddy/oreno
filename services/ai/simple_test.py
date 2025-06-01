"""
Simple test script for Ollama integration without Django dependencies.
"""
import requests
import json

# Configuration
OLLAMA_BASE_URL = "http://localhost:11434"
OLLAMA_MODEL = "llama3"

def check_ollama_running():
    """Check if Ollama is running by checking the server"""
    try:
        response = requests.get(f"{OLLAMA_BASE_URL}/api/tags")
        if response.status_code == 200:
            models = response.json().get("models", [])
            print("\n=== Ollama Status: RUNNING ===")
            if models:
                print(f"Available models: {[model['name'] for model in models]}")
            else:
                print("No models found. You may need to pull a model with 'ollama pull llama3'")
            return True
        else:
            print("\n=== Ollama Status: NOT RESPONDING CORRECTLY ===")
            print(f"Status code: {response.status_code}")
            return False
    except Exception as e:
        print("\n=== Ollama Status: NOT RUNNING ===")
        print(f"Error: {e}")
        return False

def test_ollama_chat(question):
    """Test Ollama chat API directly"""
    print(f"\nSending question to Ollama: {question}")
    
    # Prepare the payload for Ollama
    payload = {
        "model": OLLAMA_MODEL,
        "messages": [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": question}
        ],
        "stream": False,
        "options": {
            "temperature": 0.3,
            "num_predict": 100  # Reduced token count for faster response
        }
    }
    
    print("Payload ready, sending to API...")
    
    try:
        print("Calling Ollama API at", f"{OLLAMA_BASE_URL}/api/chat")
        # Call Ollama API with shorter timeout
        response = requests.post(
            f"{OLLAMA_BASE_URL}/api/chat",
            headers={"Content-Type": "application/json"},
            data=json.dumps(payload),
            timeout=30  # 30 second timeout
        )
        print("Received response from API")
        
        if response.status_code == 200:
            result = response.json()
            print("Raw API response:", result)
            answer = result.get("message", {}).get("content", "").strip()
            print("\n=== Ollama Response ===")
            print(answer)
            return answer
        else:
            print(f"\n=== Error: {response.status_code} ===")
            print(response.text)
            return None
    
    except Exception as e:
        print(f"\n=== Error: {e} ===")
        return None

if __name__ == "__main__":
    # Check if Ollama is running
    if check_ollama_running():
        # Test with a very simple question
        test_ollama_chat("Hello, are you working?")
    else:
        print("Please make sure Ollama is running with 'ollama serve' before testing.")
