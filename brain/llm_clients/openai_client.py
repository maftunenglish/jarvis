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

def get_llm_response(user_input: str, context: list = None) -> str:
    """
    Enhanced to use conversation context.
    """
    try:
        # Prepare message history with context
        messages = [{"role": "system", "content": JARVIS_PROMPT}]
        
        # Add conversation context if provided
        if context:
            for exchange in context[-3:]:  # Last 3 exchanges only
                messages.append({"role": "user", "content": exchange['user']})
                messages.append({"role": "assistant", "content": exchange['ai']})
        
        # Add the current user input
        messages.append({"role": "user", "content": user_input})
        
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages
        )
        return response.choices[0].message.content.strip()
        
    except Exception as e:
        return f"I apologize, but I encountered an error: {str(e)}"