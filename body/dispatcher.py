# body/dispatcher.py
from body.tools.system_control import get_time, get_date
from body.tools.google_keep import create_note
from body.tools.memory_management import remember_fact, recall_fact  # New imports

def dispatch_command(user_input):
    user_input_lower = user_input.lower()
    
    # Existing tools
    if "time" in user_input_lower:
        return get_time()
    if "date" in user_input_lower:
        return get_date()
    if any(word in user_input_lower for word in ['note', 'remember', 'remind me','keep in mind', ]):
        # ... existing note code ...
    
    # NEW: Long-term memory commands
    if any(word in user_input_lower for word in ['remember that', 'my', 'is', 'i like', 'i love']):
        return remember_fact(user_input)
    
    if any(word in user_input_lower for word in ['what is my', 'what was my' ,'what i was said']):
        return recall_fact(user_input)
    
    return None