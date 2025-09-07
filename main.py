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

# NEW: Import chat logging and learning modules
try:
    from memory.chat_logger import ChatLogger
    from brain.chat_learner import ChatHistoryLearner
    CHAT_LOGGING_AVAILABLE = True
except ImportError as e:
    CHAT_LOGGING_AVAILABLE = False
    print(f"ℹ️  Chat logging modules not available: {e} - continuing without them")

# Force import API keys from .env on startup
imported_count = api_manager.import_keys_from_env()
if imported_count > 0:
    print(f"✅ Imported {imported_count} API keys from environment")
else:
    print("❌ No API keys found in environment. Use 'add api key' command.")

# Register cleanup function
import atexit

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
    # NEW: Initialize chat logging and learning if available
    if CHAT_LOGGING_AVAILABLE:
        chat_logger = ChatLogger()
        chat_learner = ChatHistoryLearner()
        chat_logger.start_new_session()
        message_count = 0
        learn_counter = 0
        
        # Register cleanup
        atexit.register(chat_logger.stop)

    mode = select_interface_mode()

    # Use personality-specific greeting
    greeting = get_personality_greeting()
    if mode == "voice":
        speak(greeting)
    else:
        print(f"AI: {greeting}")

    # NEW: Log the greeting if chat logging is available
    if CHAT_LOGGING_AVAILABLE:
        chat_logger.log_message("ai", greeting)

    while True:
        user_input = get_user_input(mode)
        if not user_input:
            if mode == "voice":
                continue
            else:
                break

        # NEW: Log user message if chat logging is available
        if CHAT_LOGGING_AVAILABLE:
            chat_logger.log_message("user", user_input)
            message_count += 1

        if user_input.lower() in ["quit", "exit", "shutdown"]:
            # Use personality-specific farewell
            farewell = get_personality_farewell()
            if mode == "voice":
                speak(farewell)
            else:
                print(f"AI: {farewell}")
            
            # NEW: Save session and learn before exiting
            if CHAT_LOGGING_AVAILABLE:
                chat_logger.log_message("ai", farewell)
                chat_logger.save_session()
                if learn_counter >= 24:  # Learn once per day equivalent
                    learning_results = chat_learner.learn_from_recent_sessions(days=3, max_sessions=10)
                    print(f"📚 Learned {learning_results['facts_learned']} facts from {learning_results['sessions_processed']} sessions")
            break

        if user_input.lower() in ["switch mode", "change mode"]:
            mode = "text" if mode == "voice" else "voice"
            # Use personality-specific mode switch message
            mode_message = get_personality_mode_switch(mode)
            if mode == "voice":
                speak(mode_message)
            else:
                print(f"AI: {mode_message}")
            
            # NEW: Log mode switch message
            if CHAT_LOGGING_AVAILABLE:
                chat_logger.log_message("ai", mode_message)
            continue

        # Process command (EXISTING CODE UNCHANGED)
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

        # Add to conversation history (EXISTING CODE UNCHANGED)
        add_to_history(user_input, personality_response)

        # NEW: Log AI response and handle periodic saving/learning
        if CHAT_LOGGING_AVAILABLE:
            chat_logger.log_message("ai", personality_response)
            message_count += 1
            
            # Save session every 10 messages
            if message_count >= 10:
                chat_logger.save_session()
                message_count = 0
            
            # Learn from chats every 24 messages (simulating once per day)
            learn_counter += 1
            if learn_counter >= 24:
                learning_results = chat_learner.learn_from_recent_sessions(days=3, max_sessions=10)
                print(f"📚 Learned {learning_results['facts_learned']} facts from {learning_results['sessions_processed']} sessions")
                learn_counter = 0

if __name__ == "__main__":
    main()