# brain/llm_clients/openai_client.py
from openai import OpenAI
from config.settings import settings
import yaml
import os
from brain.api_manager import api_manager  # ← UNCOMMENT THIS LINE
from memory.short_term import get_recent_history

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
    Enhanced to use conversation context with API failover.
    """
    max_retries = 3
    retry_count = 0
    
    while retry_count < max_retries:
        try:
            # Get next available API key from manager ← NEW CODE
            api_key = api_manager.get_next_available_key('openai')
            
            if not api_key:
                return "All API keys are currently rate-limited. Please try again later, Sir."
            
            # Create client with the obtained key ← NEW CODE
            client = OpenAI(api_key=api_key)
            
            # Prepare message history with context
            messages = [{"role": "system", "content": JARVIS_PROMPT}]
            
            # Add conversation context if provided
            if context:
                for exchange in context[-3:]:
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
            error_msg = str(e)
            
            # Check if rate limit error ← NEW CODE
            if "rate limit" in error_msg.lower() or "429" in error_msg:
                print(f"Rate limit hit on key. Marking as limited.")
                api_manager.mark_key_rate_limited(api_key)
                retry_count += 1
                continue
            elif "invalid" in error_msg.lower() or "401" in error_msg:
                print(f"Invalid API key. Marking as invalid.")
                api_manager.mark_key_rate_limited(api_key)
                retry_count += 1
                continue
            else:
                return f"I apologize, but I encountered an error: {error_msg}"
    
    return "All API retries failed. Please try again later, Sir."