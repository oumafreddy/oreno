import os
from .ollama_adapter import ask_ollama
# Keep OpenAI as a fallback
from .llm_adapter import ask_llm

# Example FAQ knowledge base (could be loaded from a file or DB)
FAQ_KB = [
    {
        'question': 'how do i use the legal app',
        'answer': 'The Legal app in Oreno GRC helps you manage contracts and legal documents. You can create, review, and store legal documents securely. To get started, go to the Legal app from the dashboard and follow the on-screen instructions.'
    },
    {
        'question': 'what does the risk app do',
        'answer': 'The Risk app allows you to identify, assess, and monitor risks within your organization. You can create risk registers, assign owners, and track mitigation actions.'
    },
    {
        'question': 'how do i get started',
        'answer': 'Welcome to Oreno GRC! Start by exploring the dashboard. Each app (Audit, Risk, Legal, Compliance, etc.) is accessible from the main menu. Click on any app to see its features and guides.'
    },
    # Add more FAQ entries as needed
]

def find_faq_answer(question: str) -> str:
    q = question.lower().strip()
    for entry in FAQ_KB:
        if entry['question'] in q:
            return entry['answer']
    return None

def ai_assistant_answer(question: str, user, org) -> str:
    faq_answer = find_faq_answer(question)
    if faq_answer:
        return faq_answer
    
    # Add a special message for unauthenticated users
    if user is None:
        # Only answer general questions for unauthenticated users
        context = "This is an unauthenticated user. Only provide general information about GRC best practices or general platform functionality. Do not reference any specific organization data."
        try:
            return ask_ollama(question, user, org, context=context)
        except Exception as e:
            import logging
            logging.getLogger('services.ai.ai_service').error(f"Ollama error: {e}, falling back to OpenAI")
            return ask_llm(question, user, org, context=context)
    
    # 2. Use Ollama for best practice/platform Q&A with OpenAI fallback
    try:
        return ask_ollama(question, user, org)
    except Exception as e:
        import logging
        logging.getLogger('services.ai.ai_service').error(f"Ollama error: {e}, falling back to OpenAI")
        return ask_llm(question, user, org)
