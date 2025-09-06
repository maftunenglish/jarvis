# brain/orchestrator.py
"""
Orchestrator: routes tasks between tools, memory, and LLMs.
"""

from brain.llm_clients.openai_client import OpenAIClient

# Create a single shared OpenAI client instance
openai_client = OpenAIClient(model="gpt-3.5-turbo")  # You can change model here

def route_task(user_input: str, context=None) -> str:
    """
    Decide how to handle user input:
      - If it's a general query, forward to the LLM.
      - If context (chat history) is provided, include it in the prompt.
    """
    messages = []

    # Add context history if available
    if context:
        for exchange in context:
            messages.append({"role": "user", "content": exchange["user"]})
            messages.append({"role": "assistant", "content": exchange["ai"]})

    # Add the new user input
    messages.append({"role": "user", "content": user_input})

    # Ask the LLM
    try:
        resp = openai_client.chat_completion(messages=messages)
        return resp["choices"][0]["message"]["content"]
    except Exception as e:
        return f"❌ LLM error: {str(e)}"
