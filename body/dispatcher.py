# body/dispatcher.py
from body.tools.system_control import get_time, get_date
from body.tools.memory_management import remember_fact, recall_fact
from memory.short_term import get_recent_history
from memory.long_term import long_term_memory
from brain.api_manager import api_manager  # NEW IMPORT

# Google Keep is optional since we're skipping it for now
google_keep_available = False

def dispatch_command(user_input):
    user_input_lower = user_input.lower()
    
    # Existing tools
    if "time" in user_input_lower:
        return get_time()
        
    if "date" in user_input_lower:
        return get_date()
    
    # NEW: API Management Commands
    if user_input_lower.startswith('add api key '):
        parts = user_input.split(' ')
        try:
            if len(parts) >= 6 and parts[3] == 'priority':
                service = parts[2]
                api_key = parts[4]
                priority = int(parts[5])
                success = api_manager.add_api_key(service, api_key, priority)
                if success:
                    return f"Added {service} API key with priority {priority}, Sir."
                else:
                    return "API key already exists, Sir."
            else:
                # Default priority if not specified
                service = 'openai'
                api_key = parts[3]
                priority = 99  # Low priority for manually added keys
                success = api_manager.add_api_key(service, api_key, priority)
                if success:
                    return f"Added {service} API key with default priority, Sir."
                else:
                    return "API key already exists, Sir."
        except Exception as e:
            return f"Error adding API key: {str(e)}"
    
    if user_input_lower == 'list api keys':
        status = api_manager.get_key_status('openai')
        if not status:
            return "No API keys configured, Sir."
        
        response = "🔑 Configured API Keys:\n"
        for key in status:
            status_icon = "✅" if key['status'] == 'active' else "⏸️" if key['status'] == 'rate_limited' else "❌"
            response += f"{status_icon} Priority {key['priority']}: {key['api_key']} (Used {key['usage_count']} times)\n"
        return response
    
    if user_input_lower.startswith('remove api key '):
        parts = user_input.split(' ')
        if len(parts) >= 4:
            try:
                priority_to_remove = int(parts[3])
                success = api_manager.remove_api_key(priority_to_remove)
                if success:
                    return f"Removed API key with priority {priority_to_remove}, Sir."
                else:
                    return f"No API key found with priority {priority_to_remove}, Sir."
            except Exception as e:
                return f"Error removing API key: {str(e)}"
    
    # Memory commands
    if any(word in user_input_lower for word in ['remember that', 'my', 'is', 'i like', 'i love', 'my name is']):
        memory_response = remember_fact(user_input)
        if memory_response and "didn't detect" not in memory_response:
            return memory_response
        # If no fact was detected, let it fall through to LLM
    
    if any(word in user_input_lower for word in ['what is my', 'what was my']):
        memory_response = recall_fact(user_input)
        if memory_response:
            return memory_response
    
    # Debug commands
    if user_input_lower == "debug history":
        history = get_recent_history()
        if history:
            response = "Recent conversation history:\n"
            for i, exchange in enumerate(history[-3:], 1):
                response += f"{i}. You: {exchange['user']}\n"
                response += f"   AI: {exchange['ai']}\n"
            return response
        return "No recent conversation history."
    
    if user_input_lower == "debug memory":
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