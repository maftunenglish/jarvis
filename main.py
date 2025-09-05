# main.py
from brain.llm_clients.openai_client import get_llm_response
from body.dispatcher import dispatch_command  # Import the dispatcher

def main():
    print("🤖 Your Personal AI is now active. Type 'quit' to exit.")
    
    while True:
        user_input = input("You: ")
        
        if user_input.lower() in ['quit', 'exit', 'bye']:
            print("AI: Goodbye.")
            break
        
        # FIRST, try to dispatch the command to a tool
        tool_response = dispatch_command(user_input)
        
        if tool_response is not None:
            # If dispatcher handled it (returned a response), use that
            print(f"AI: {tool_response}")
        else:
            # If dispatcher returned None, send it to the LLM Brain
            ai_response = get_llm_response(user_input)
            print(f"AI: {ai_response}")

if __name__ == "__main__":
    main()