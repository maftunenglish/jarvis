# interfaces/input_manager.py
from interfaces.voice_input import listen_for_command
from interfaces.voice_output import speak

def get_user_input(mode):
    """
    Gets user input based on the selected mode.
    
    Args:
        mode (str): 'voice' or 'text'
        
    Returns:
        str: User's input, or None if no input/exit command
    """
    if mode == 'voice':
        print("🎙️  Voice mode active...")
        return listen_for_command()
    else:
        # Text mode
        try:
            user_input = input("You: ").strip()
            return user_input if user_input else None
        except EOFError:
            return None

def select_interface_mode():
    """
    Presents a menu to select the input mode.
    
    Returns:
        str: Selected mode ('voice' or 'text')
    """
    print("\n" + "="*40)
    print("        J.A.R.V.I.S. INTERFACE MENU")
    print("="*40)
    print("1. Voice Mode (Hands-free operation)")
    print("2. Text Mode (Discrete communication)")
    print("="*40)
    
    while True:
        choice = input("Select mode (1 or 2): ").strip()
        if choice == '1':
            speak("Voice mode activated. I am listening, Sir.")
            return 'voice'
        elif choice == '2':
            print("Text mode activated. You may begin typing, Sir.")
            return 'text'
        else:
            print("Invalid selection. Please choose 1 or 2.")