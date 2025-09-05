# brain/llm_clients/openai_client.py
from openai import OpenAI
from config.settings import settings
import yaml
import os
from memory.short_term import get_recent_history

client = OpenAI(api_key=settings.OPENAI_API_KEY)

def load_jarvis_persona():
    """Loads the Jarvis personality prompt from the YAML file."""
    try:
        persona_path = os.path.join('config', 'personas', 'jarvis.yaml')
        with open(persona_path, 'r') as file:
            data = yaml.safe_load(file)
            return data.get('system_prompt', 'You are a helpful assistant.')
    except FileNotFoundError:
        print("Jarvis persona file not found. Using default prompt.")
        return "You are a helpful assistant."

JARVIS_PROMPT = load_jarvis_persona()

def get_llm_response(user_input: str) -> str:
    """
    Advanced context management with token optimization.
    """
    try:
        history = get_recent_history()
        messages = [{"role": "system", "content": JARVIS_PROMPT}]
        
        # Smart context selection: prioritize recent exchanges but keep under reasonable limit
        total_chars = 0
        max_context_chars = 2000  # Limit context to ~1000 characters
        
        # Add history from newest to oldest until we hit the limit
        for exchange in reversed(history):
            exchange_chars = len(exchange['user']) + len(exchange['ai'])
            if total_chars + exchange_chars > max_context_chars:
                break
            messages.insert(1, {"role": "assistant", "content": exchange['ai']})
            messages.insert(1, {"role": "user", "content": exchange['user']})
            total_chars += exchange_chars
        
        messages.append({"role": "user", "content": user_input})
        
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            max_tokens=1000
        )
        return response.choices[0].message.content.strip()
        
    except Exception as e:
        return f"I apologize, but I encountered an error: {str(e)}"