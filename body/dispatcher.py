# body/dispatcher.py
from body.tools.system_control import get_time, get_date
from body.tools.memory_management import remember_fact, recall_fact

# Google Keep is optional since we're skipping it for now
google_keep_available = False

def dispatch_command(user_input):
    user_input_lower = user_input.lower()
    
    # Existing tools
    if "time" in user_input_lower:
        return get_time()
        
    if "date" in user_input_lower:
        return get_date()
        
    # Google Keep commands (optional)
    if google_keep_available and any(word in user_input_lower for word in ['note', 'remember', 'remind me']):
        # Note: Google Keep implementation would go here
        pass
    
    # Memory commands
    if any(word in user_input_lower for word in ['remember that', 'my', 'is', 'i like', 'i love']):
        return remember_fact(user_input)
    
    if any(word in user_input_lower for word in ['what is my', 'what was my']):
        return recall_fact(user_input)
    
    # If no tool matches, return None to send to LLM
    return None