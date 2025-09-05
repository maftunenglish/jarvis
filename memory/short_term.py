# memory/short_term.py
from collections import deque

# Store the last 6 exchanges for context (increased from 5 for better context)
conversation_history = deque(maxlen=6)

def add_to_history(user_input, ai_response):
    """
    Adds a conversation turn to the short-term memory.
    
    Args:
        user_input (str): The user's message
        ai_response (str): The AI's response
    """
    conversation_history.append({"user": user_input, "ai": ai_response})

def get_recent_history():
    """
    Retrieves the recent conversation history for context.
    
    Returns:
        list: The last few conversation turns
    """
    return list(conversation_history)

def clear_history():
    """
    Clears the conversation history.
    """
    conversation_history.clear()

def get_formatted_history():
    """
    Returns the conversation history in a formatted string for LLM context.
    """
    if not conversation_history:
        return ""
    
    formatted = "\nRecent conversation history:\n"
    for exchange in conversation_history:
        formatted += f"User: {exchange['user']}\n"
        formatted += f"Assistant: {exchange['ai']}\n"
    
    return formatted