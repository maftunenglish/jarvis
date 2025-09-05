# main.py
from brain.llm_clients.openai_client import get_llm_response

def main():
    print("🤖 Your Personal AI is now active. Type 'quit' to exit.")
    
    while True:
        # Get input from the user
        user_input = input("You: ")
        
        # Check if the user wants to quit
        if user_input.lower() in ['quit', 'exit', 'bye']:
            print("AI: Goodbye.")
            break
        
        # Get the AI's response by calling our function
        ai_response = get_llm_response(user_input)
        
        # Print the AI's response
        print(f"AI: {ai_response}")

# This line ensures the code runs only when executed directly
if __name__ == "__main__":
    main()