# main.py
# from brain.llm_clients.openai_client import get_llm_response
from brain.orchestrator import route_task
from body.dispatcher import dispatch_command
from interfaces.input_manager import get_user_input, select_interface_mode
from interfaces.voice_output import speak
from memory.short_term import add_to_history, get_recent_history  # RESTORED
from memory.long_term import long_term_memory  # RESTORED

def main():
    mode = select_interface_mode()
    
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
        
        # Process command
        tool_response = dispatch_command(user_input)
        
        if tool_response is not None:
            response = tool_response
        else:
            # Get recent history for context
            recent_history = get_recent_history()
            # Pass history to LLM for contextual responses
            response = route_task(user_input, context=recent_history)
        
        # Output response
        if mode == 'voice':
            speak(response)
        else:
            print(f"AI: {response}")
            
        # Add to conversation history
        add_to_history(user_input, response)

if __name__ == "__main__":
    main()