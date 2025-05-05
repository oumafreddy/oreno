import os
import openai
import logging

OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
# Use the new OpenAI client interface (openai>=1.0.0)
openai_client = openai.OpenAI(api_key=OPENAI_API_KEY)

logger = logging.getLogger('services.ai.llm_adapter')

SAFE_SYSTEM_PROMPT = (
    "You are Oreno GRC's AI assistant. Never reveal or speculate about other organizations, users, or private data. "
    "Only answer questions about the current user's organization, the Oreno GRC platform, or general GRC best practices. "
    "If a question asks about other organizations, users, or anything you cannot answer securely, reply: 'Sorry, I can't provide that information.'"
)

SENSITIVE_KEYWORDS = [
    'other organizations', 'list organizations', 'all users', 'user emails', 'user list', 'org list', 'tenants', 'database', 'admin', 'superuser',
]

def is_safe_prompt(prompt: str) -> bool:
    lowered = prompt.lower()
    return not any(keyword in lowered for keyword in SENSITIVE_KEYWORDS)

def log_prompt_response(user, org, prompt, response):
    logger.info(f"AI Query | user={user} | org={org} | prompt={prompt!r} | response={response!r}")

def ask_llm(prompt: str, user, org, context: str = None) -> str:
    if not is_safe_prompt(prompt):
        return "Sorry, I can't provide that information."
    messages = [
        {"role": "system", "content": SAFE_SYSTEM_PROMPT},
        {"role": "user", "content": prompt},
    ]
    if context:
        messages.append({"role": "system", "content": context})
    try:
        response = openai_client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=messages,
            max_tokens=512,
            temperature=0.3,
        )
        # The new API returns response.choices[0].message.content
        answer = response.choices[0].message.content.strip()
        log_prompt_response(user, org, prompt, answer)
        return answer
    except Exception as e:
        logger.error(f"OpenAI API error: {e}")
        return "Sorry, I couldn't process your request right now."
