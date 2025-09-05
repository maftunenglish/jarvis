# body/dispatcher.py
from body.tools.system_control import get_time

def dispatch_command(user_input):
    """
    Analyzes user input and decides whether to handle it with a tool
    or send it to the LLM brain.
    
    Returns:
        str: The tool's response if handled, None if should go to LLM
    """
    user_input_lower = user_input.lower()
    
    # Check for time request
    if "time" in user_input_lower:
        return get_time()
        
    # Add more tool checks here in the future...
    
    # If no tool matches, return None to send to LLM
    return None