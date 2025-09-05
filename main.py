# main.py
from brain.llm_clients.openai_client import get_llm_response
from body.dispatcher import dispatch_command
from memory.short_term import add_to_history, get_recent_history
from interfaces.input_manager import get_user_input, select_interface_mode
from interfaces.voice_output import speak

def main():
    # Select interface mode
    mode = select_interface_mode()
    
    # Initial greeting based on mode
    if mode == 'voice':
        speak("All systems operational. How may I assist you, Sir?")
    else:
        print("AI: Systems ready. How may I assist you, Sir?")
    
    while True:
        # Get input based on selected mode
        user_input = get_user_input(mode)
        
        if not user_input:
            if mode == 'voice':
                continue  # Keep listening in voice mode
            else:
                break     # Exit on empty text input
        
        # Check for exit commands or mode switch
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
        
        # Process the command
        tool_response = dispatch_command(user_input)
        
        if tool_response is not None:
            response = tool_response
        else:
            response = get_llm_response(user_input)
        
        # Output based on mode
        if mode == 'voice':
            speak(response)
        else:
            print(f"AI: {response}")
            
        # Add to conversation history
        add_to_history(user_input, response)

if __name__ == "__main__":
    main()