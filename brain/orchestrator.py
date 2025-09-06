# brain/orchestrator.py
"""
Orchestrator: routes tasks between tools, memory, and LLMs.
"""

# Choose ONE of these options:

# OPTION 1: Use Gemini
from brain.llm_clients.gemini_client import get_gemini_response

# OPTION 2: Use OpenAI 
from brain.llm_clients.openai_client import get_llm_response

# OPTION 3: Use DeepSeek
# from brain.llm_clients.deepseek_client import get_deepseek_response

def route_task(user_input: str, context=None) -> str:
    """
    Decide how to handle user input:
      - If it's a general query, forward to the LLM.
      - If context (chat history) is provided, include it in the prompt.
    """
    
    # Ask the LLM
    try:
        # OPTION 1: Use Gemini
        response = get_gemini_response(user_input, context)
        
        # OPTION 2: Use OpenAI (uncomment if using OpenAI)
        response = get_llm_response(user_input, context)
        
        # OPTION 3: Use DeepSeek (uncomment if using DeepSeek)
        # response = get_deepseek_response(user_input, context)
        
        return response
    except Exception as e:
        return f"❌ LLM error: {str(e)}"