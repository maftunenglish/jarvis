# brain/llm_clients/openai_client.py
from openai import OpenAI
from config.settings import settings
import yaml
import os

# Initialize the OpenAI client
client = OpenAI(api_key=settings.OPENAI_API_KEY)


def load_jarvis_persona():
    """Loads the Jarvis personality prompt from the YAML file."""
    try:
        persona_path = os.path.join("config", "personas", "jarvis.yaml")
        with open(persona_path, "r") as file:
            data = yaml.safe_load(file)
            return data.get("system_prompt", "You are a helpful assistant.")
    except FileNotFoundError:
        print("Jarvis persona file not found. Using default prompt.")
        return "You are a helpful assistant."


# Load the persona at startup
JARVIS_PROMPT = load_jarvis_persona()


def get_llm_response(user_input: str) -> str:
    """
    Sends a user's message to the GPT model using the Jarvis personality.

    Args:
        user_input (str): The message from the user.

    Returns:
        str: The AI's response text.
    """
    try:
        # Send the request to the OpenAI API with Jarvis personality
        response = client.chat.completions.create(
            model="gpt-4o-mini",  # Lightweight GPT-4 class model, better than 3.5
            messages=[
                {"role": "system", "content": JARVIS_PROMPT},  # Jarvis personality
                {"role": "user", "content": user_input},  # User message
            ],
        )
        # Extract and return the text from the response
        return response.choices[0].message.content.strip()

    except Exception as e:
        # Return a helpful error message if something goes wrong
        return f"I apologize, but I encountered an error: {str(e)}"
