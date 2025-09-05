# body/dispatcher.py
from body.tools.system_control import get_time, get_date
from body.tools.memory_management import remember_fact, recall_fact
from memory.short_term import get_recent_history
from memory.long_term import long_term_memory

# Google Keep is optional since we're skipping it for now
google_keep_available = False

def dispatch_command(user_input):
    user_input_lower = user_input.lower()
    
    # Existing tools
    if "time" in user_input_lower:
        return get_time()
        
    if "date" in user_input_lower:
        return get_date()
    
    # NEW: Memory commands - THIS IS WHAT WAS MISSING
    if any(word in user_input_lower for word in ['remember that', 'my', 'is', 'i like', 'i love', 'my name is']):
        memory_response = remember_fact(user_input)
        if memory_response and "didn't detect" not in memory_response:
            return memory_response
        # If no fact was detected, let it fall through to LLM
    
    if any(word in user_input_lower for word in ['what is my', 'what was my']):
        memory_response = recall_fact(user_input)
        if memory_response:
            return memory_response
    
    # NEW: Debug commands to test memory
    if user_input_lower == "debug history":
        history = get_recent_history()
        if history:
            response = "Recent conversation history:\n"
            for i, exchange in enumerate(history[-3:], 1):  # Show last 3 exchanges
                response += f"{i}. You: {exchange['user']}\n"
                response += f"   AI: {exchange['ai']}\n"
            return response
        return "No recent conversation history."
    
    if user_input_lower == "debug memory":
        # Test if memory system is working by trying to store and recall a test fact
        try:
            long_term_memory.add_fact('user', 'test_attribute', 'test_value')
            fact = long_term_memory.get_current_fact('user', 'test_attribute')
            if fact and fact['value'] == 'test_value':
                return "✅ Long-term memory system is operational and working correctly."
            else:
                return "❌ Long-term memory system test failed."
        except Exception as e:
            return f"❌ Long-term memory error: {str(e)}"
    
    # If no tool matches, return None to send to LLM
    return None