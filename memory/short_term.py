# memory/short_term.py
from collections import deque

# Store the last 5 exchanges for context
conversation_history = deque(maxlen=10)

def add_to_history(user_input, ai_response):
    """
    Adds a conversation turn to the short-term memory.
    """
    conversation_history.append({"user": user_input, "ai": ai_response})

def get_recent_history():
    """
    Retrieves the recent conversation history for context.
    
    Returns:
        list: The last few conversation turns.
    """
    return list(conversation_history)

def clear_history():
    """
    Clears the conversation history.
    """
    conversation_history.clear()