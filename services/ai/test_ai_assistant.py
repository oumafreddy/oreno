import os
import sys
import dotenv
from pathlib import Path
import subprocess

# Load environment variables from .env.oreno
env_file = Path('/opt/GRC/oreno/.env.oreno')
if env_file.exists():
    dotenv.load_dotenv(env_file)
    print("Loaded environment from .env.oreno")
else:
    print("Warning: .env.oreno file not found")

# Check if Ollama is running
try:
    result = subprocess.run(['pgrep', 'ollama'], capture_output=True, text=True)
    if result.returncode == 0:
        print("Ollama is running!")
    else:
        print("WARNING: Ollama is not running!")
        subprocess.run(['ollama', 'serve'], start_new_session=True)
        print("Started Ollama service")
except Exception as e:
    print(f"Error checking Ollama status: {e}")

# List available models
try:
    result = subprocess.run(['ollama', 'list'], capture_output=True, text=True)
    print("\nAvailable Ollama models:")
    print(result.stdout)
except Exception as e:
    print(f"Error listing Ollama models: {e}")

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

# Import Django and setup
import django
django.setup()

# Now import and test the AI assistant
from services.ai.ai_service import ai_assistant_answer
from services.ai.ollama_adapter import ask_ollama

# Test Ollama directly
print("\n=== Testing Ollama directly ===")
test_question = "What is GRC and how can it help my organization?"
print(f"Question: {test_question}")
try:
    response = ask_ollama(test_question, user=None, org=None)
    print("\nOllama Response:")
    print(response)
except Exception as e:
    print(f"Error using Ollama: {e}")

# Test through AI service for unauthenticated user
print("\n=== Testing AI Assistant Service (unauthenticated) ===")
print(f"Question: {test_question}")
try:
    response = ai_assistant_answer(test_question, user=None, org=None)
    print("\nAI Assistant Response (unauthenticated):")
    print(response)
except Exception as e:
    print(f"Error using AI assistant: {e}")

# Test through AI service for authenticated user
print("\n=== Testing AI Assistant Service (authenticated) ===")
class MockUser:
    def __init__(self, id, email):
        self.id = id
        self.email = email

class MockOrg:
    def __init__(self, id, name):
        self.id = id
        self.name = name

mock_user = MockUser(1, "test@example.com")
mock_org = MockOrg(1, "Test Organization")
try:
    response = ai_assistant_answer(test_question, user=mock_user, org=mock_org)
    print("\nAI Assistant Response (authenticated):")
    print(response)
except Exception as e:
    print(f"Error using AI assistant with authenticated user: {e}")
