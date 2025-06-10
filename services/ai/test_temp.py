import requests
import json

def ask_ollama(prompt, temperature=0.1):
    """
    Test function to ask Ollama with a specific temperature
    """
    # Prepare the payload for Ollama
    payload = {
        "model": "tinyllama",
        "prompt": prompt,
        "stream": False,
        "options": {
            "temperature": temperature,
        }
    }
    
    try:
        # Call Ollama API
        response = requests.post(
            "http://localhost:11434/api/generate",
            headers={"Content-Type": "application/json"},
            data=json.dumps(payload),
            timeout=60
        )
        
        if response.status_code == 200:
            result = response.json()
            return result.get("response", "").strip()
        else:
            return f"Error: {response.status_code} - {response.text}"
    
    except Exception as e:
        return f"Error: {e}"

# Test with a GRC question
context = """
GRC stands for Governance, Risk, and Compliance.
- Governance refers to the management and leadership structures and processes that ensure an organization meets its objectives.
- Risk management involves identifying, assessing, and mitigating risks to the organization.
- Compliance means ensuring the organization adheres to all relevant laws, regulations, and standards.
"""

question = "What is GRC and how can it help my organization?"
full_prompt = context + "\n\nQuestion: " + question

# Test with different temperature settings
print("\n--- Testing with temperature=0.1 ---")
response_low_temp = ask_ollama(full_prompt, temperature=0.1)
print(response_low_temp)

print("\n--- Testing with temperature=0.7 ---")
response_high_temp = ask_ollama(full_prompt, temperature=0.7)
print(response_high_temp)
