# main.py
from brain.llm_clients.openai_client import get_llm_response
from body.dispatcher import dispatch_command
from interfaces.input_manager import get_user_input, select_interface_mode
from interfaces.voice_output import speak
from memory.short_term import add_to_history
from brain.memory_orchestrator import memory_orchestrator  # NEW
from memory.long_term import long_term_memory  # NEW

def main():
    mode = select_interface_mode()
    
    # NEW: Display memory summary on startup
    memory_summary = long_term_memory.get_memory_summary()
    print(f"Memory Summary: {memory_summary}")
    
    if mode == 'voice':
        speak("All systems operational. How may I assist you, Sir?")
    else:
        print("AI: Systems ready. How may I assist you, Sir?")
    
    while True:
        user_input = get_user_input(mode)
        if not user_input:
            if mode == 'voice': continue
            else: break
        
        if user_input.lower() in ['quit', 'exit', 'shutdown']:
            if mode == 'voice':
                speak("Shutting down systems. Goodbye, Sir.")
            else:
                print("AI: Shutting down systems. Goodbye, Sir.")
            break
            
        if user_input.lower() in ['switch mode', 'change mode']:
            mode = 'text' if mode == 'voice' else 'voice'
            status = "switching to text mode" if mode == 'text' else "switching to voice mode"
            if mode == 'voice':
                speak(f"Understood, Sir. {status}.")
            else:
                print(f"AI: Understood, Sir. {status}.")
            continue
        
        # NEW: Get memory context for better responses
        memory_context = memory_orchestrator.get_memory_context(user_input)
        
        # Process command (existing functionality preserved)
        tool_response = dispatch_command(user_input)
        
        if tool_response is not None:
            response = tool_response
        else:
            # NEW: Pass memory context to LLM
            enhanced_input = f"Memory context: {memory_context}\n\nUser: {user_input}"
            response = get_llm_response(enhanced_input)
        
        # NEW: Intelligent memory extraction
        memory_result = memory_orchestrator.extract_and_store_memory(user_input, response)
        if memory_result['stored_count'] > 0:
            print(f"📝 Auto-remembered {memory_result['stored_count']} facts")
        
        # Output response
        if mode == 'voice':
            speak(response)
        else:
            print(f"AI: {response}")
            
        add_to_history(user_input, response)

if __name__ == "__main__":
    main()