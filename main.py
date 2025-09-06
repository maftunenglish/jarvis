# main.py
from brain.orchestrator import route_task
from body.dispatcher import dispatch_command
from interfaces.input_manager import get_user_input, select_interface_mode
from interfaces.voice_output import speak
from memory.short_term import add_to_history, get_recent_history
from memory.long_term import long_term_memory
from brain.api_manager import api_manager
from brain.llm_clients.deepseek_client import get_deepseek_response as get_llm_response

# Import J.A.R.V.I.S. personality configuration
from brain.utils.config_loader import config_loader

# Force import API keys from .env on startup
imported_count = api_manager.import_keys_from_env()
if imported_count > 0:
    print(f"✅ Imported {imported_count} API keys from environment")
else:
    print("❌ No API keys found in environment. Use 'add api key' command.")

def get_personality_greeting():
    """Get appropriate greeting based on time of day from personality config"""
    return config_loader.get_greeting()

def get_personality_farewell():
    """Get personality-appropriate farewell message"""
    return "Shutting down systems. Goodbye, Sir."

def get_personality_mode_switch(mode):
    """Get personality-appropriate mode switch message"""
    status = "switching to text mode" if mode == "text" else "switching to voice mode"
    return f"Understood, Sir. {status}."

def apply_personality_response(response):
    """Apply J.A.R.V.I.S. personality filters to responses"""
    # Remove emojis if disabled
    if not config_loader.should_use_emojis():
        import re
        emoji_pattern = re.compile(
            "["
            u"\U0001F600-\U0001F64F"  # emoticons
            u"\U0001F300-\U0001F5FF"  # symbols & pictographs
            u"\U0001F680-\U0001F6FF"  # transport & map symbols
            u"\U0001F1E0-\U0001F1FF"  # flags (iOS)
            "]+", flags=re.UNICODE
        )
        response = emoji_pattern.sub(r'', response)
    
    return response

def main():
    mode = select_interface_mode()

    # Use personality-specific greeting
    greeting = get_personality_greeting()
    if mode == "voice":
        speak(greeting)
    else:
        print(f"AI: {greeting}")

    while True:
        user_input = get_user_input(mode)
        if not user_input:
            if mode == "voice":
                continue
            else:
                break

        if user_input.lower() in ["quit", "exit", "shutdown"]:
            # Use personality-specific farewell
            farewell = get_personality_farewell()
            if mode == "voice":
                speak(farewell)
            else:
                print(f"AI: {farewell}")
            break

        if user_input.lower() in ["switch mode", "change mode"]:
            mode = "text" if mode == "voice" else "voice"
            # Use personality-specific mode switch message
            mode_message = get_personality_mode_switch(mode)
            if mode == "voice":
                speak(mode_message)
            else:
                print(f"AI: {mode_message}")
            continue

        # Process command
        tool_response = dispatch_command(user_input)

        if tool_response is not None:
            response = tool_response
        else:
            # Get recent history for context
            recent_history = get_recent_history()
            # Pass history to LLM for contextual responses
            response = route_task(user_input, context=recent_history)

        # Apply J.A.R.V.I.S. personality to the response
        personality_response = apply_personality_response(response)

        # Output response
        if mode == "voice":
            speak(personality_response)
        else:
            print(f"AI: {personality_response}")

        # Add to conversation history
        add_to_history(user_input, personality_response)

if __name__ == "__main__":
    main()