# brain/llm_clients/openai_client.py
from openai import OpenAI
from config.settings import settings  # Import our settings

# Initialize the OpenAI client with our API key from the config
client = OpenAI(api_key=settings.OPENAI_API_KEY)
print(settings.OPENAI_API_KEY)
def get_llm_response(user_input: str) -> str:
    """
    Sends a user's message to the GPT model and returns the response.
    
    Args:
        user_input (str): The message from the user.
        
    Returns:
        str: The AI's response text.
    """
    try:
        # Send the request to the OpenAI API
        response = client.chat.completions.create(
            model="gpt-4o-mini",  # Lightweight GPT-4 class model, better than 3.5
            messages=[{"role": "user", "content": user_input}]
        )
        # Extract and return the text from the response
        return response.choices[0].message.content.strip()
        
    except Exception as e:
        # Return a helpful error message if something goes wrong
        return f"I apologize, but I encountered an error: {str(e)}"
