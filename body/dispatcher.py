# body/dispatcher.py
# Tool imports
from .tools.system_control import get_time, get_date
from .tools.memory_management import remember_fact, recall_fact
from memory.short_term import get_recent_history
from memory.long_term import long_term_memory

# API / client manager
from brain.api_manager import api_manager
from brain.llm_clients.openai_client import get_llm_response

# Google Keep is optional since we're skipping it for now
google_keep_available = False


def _parse_add_api_key(parts: list) -> tuple:
    """
    Parse parts after "add api key".
    Returns (service, api_key, priority) or raises ValueError on bad input.
    Accepts:
      add api key <service> <api_key> priority <n>
      add api key <api_key> priority <n>    (assumes openai)
      add api key <service> <api_key>       (priority default 1)
      add api key <api_key>                 (service=openai, priority=1)
    """
    if not parts:
        raise ValueError("No arguments provided. Usage: add api key <service?> <api_key> priority <n?>")

    # defaults
    service = "openai"
    api_key = None
    priority = 1

    # copy so we can mutate
    rem = parts[:]

    # if first token looks like a known service, treat it as service
    first_low = rem[0].lower()
    known_services = {"openai", "anthropic", "deepseek", "newsapi"}
    if first_low in known_services and len(rem) >= 2:
        service = rem[0]
        api_key = rem[1]
        rest = rem[2:]
    else:
        api_key = rem[0]
        rest = rem[1:]

    # look for "priority" in rest
    rest_lower = [r.lower() for r in rest]
    if "priority" in rest_lower:
        idx = rest_lower.index("priority")
        # priority value should be next token
        if idx + 1 < len(rest):
            try:
                priority = int(rest[idx + 1])
            except Exception:
                raise ValueError("Invalid priority value. It must be an integer.")
        else:
            raise ValueError("Priority value not provided. Usage: priority <n>")

    if not api_key:
        raise ValueError("No API key provided. Usage: add api key <service?> <api_key> priority <n?>")

    return service, api_key, priority


def dispatch_command(user_input: str):
    user_input_lower = user_input.lower()
    
    if user_input_lower.startswith('add api key'):
        # Trigger API key addition workflow
        from brain.api_manager import api_manager
        # ... key addition logic here ...
        return "Please enter your API key:"

    # Existing tools
    if "time" in user_input_lower:
        return get_time()

    if "date" in user_input_lower:
        return get_date()

    # NEW: API Management Commands
    if user_input_lower.startswith("add api key "):
        # keep original-case tokens so api_key stays intact
        parts = user_input.split()
        try:
            # parts[0]=='add', parts[1]=='api', parts[2]=='key'
            remainder = parts[3:]
            service, api_key, priority = _parse_add_api_key(remainder)

            success = api_manager.add_api_key(service, api_key, priority)

            # If service is openai, sync DB keys (unmasked) into the shared client
            if service.lower() == "openai":
                client = get_openai_client()
                if hasattr(api_manager, "get_unmasked_keys"):
                    keys = api_manager.get_unmasked_keys("openai")
                    client.set_keys(keys)
                else:
                    # fallback: after adding key, still try to import from env (if any)
                    try:
                        api_manager.import_keys_from_env()
                        if hasattr(api_manager, "get_unmasked_keys"):
                            keys = api_manager.get_unmasked_keys("openai")
                            client.set_keys(keys)
                    except Exception:
                        # best-effort only
                        pass

            if success:
                return f"Added {service} API key with priority {priority}, Sir."
            else:
                return "API key already exists, Sir."
        except ValueError as ve:
            return f"Invalid add api key command: {ve}"
        except Exception as e:
            return f"Error adding API key: {str(e)}"

    if user_input_lower == "list api keys":
        status = api_manager.get_key_status("openai")
        if not status:
            return "No API keys configured, Sir."

        response = "🔑 Configured API Keys:\n"
        for key in status:
            status_icon = "✅" if key["status"] == "active" else "⏸️" if key["status"] == "rate_limited" else "❌"
            response += f"{status_icon} Priority {key['priority']}: {key['api_key']} (Used {key['usage_count']} times)\n"
        return response

    if user_input_lower.startswith("remove api key "):
        parts = user_input.split()
        if len(parts) >= 4:
            try:
                priority_to_remove = int(parts[3])
                success = api_manager.remove_api_key(priority_to_remove)

                # After removal, resync keys into client
                client = get_openai_client()
                if hasattr(api_manager, "get_unmasked_keys"):
                    keys = api_manager.get_unmasked_keys("openai")
                else:
                    keys = []
                client.set_keys(keys)

                if success:
                    return f"Removed API key with priority {priority_to_remove}, Sir."
                else:
                    return f"No API key found with priority {priority_to_remove}, Sir."
            except ValueError:
                return "Invalid priority number for remove api key."
            except Exception as e:
                return f"Error removing API key: {str(e)}"

    # Memory commands
    if any(word in user_input_lower for word in ["remember that", "my", "is", "i like", "i love", "my name is"]):
        memory_response = remember_fact(user_input)
        if memory_response and "didn't detect" not in memory_response:
            return memory_response
        # If no fact was detected, let it fall through to LLM

    if any(word in user_input_lower for word in ["what is my", "what was my"]):
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
            long_term_memory.add_fact("user", "test_attribute", "test_value")
            fact = long_term_memory.get_current_fact("user", "test_attribute")
            if fact and fact["value"] == "test_value":
                return "✅ Long-term memory system is operational and working correctly."
            else:
                return "❌ Long-term memory system test failed."
        except Exception as e:
            return f"❌ Long-term memory error: {str(e)}"

    # If no tool matches, return None to send to LLM
    return None
