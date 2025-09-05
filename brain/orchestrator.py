# brain/orchestrator.py
from brain.llm_clients.openai_client import get_llm_response

# Import with graceful fallbacks
try:
    from brain.llm_clients.deepseek_client import get_deepseek_response
    DEEPSEEK_AVAILABLE = True
except ImportError:
    DEEPSEEK_AVAILABLE = False
    print("⚠️  DeepSeek client not available. Using fallback.")

try:
    from brain.llm_clients.claude_client import get_claude_response  
    CLAUDE_AVAILABLE = True
except ImportError:
    CLAUDE_AVAILABLE = False
    print("⚠️  Claude client not available. Using fallback.")

def route_task(user_input: str, context: list = None) -> str:
    """
    Routes tasks to the most appropriate AI expert.
    Falls back to main GPT-4 if specialized models are unavailable.
    """
    user_input_lower = user_input.lower()
    
    # Coding tasks → DeepSeek Coder (if available)
    if DEEPSEEK_AVAILABLE and any(word in user_input_lower for word in [
        'code', 'program', 'function', 'script', 'python', 'javascript',
        'java', 'c++', 'html', 'css', 'react', 'algorithm', 'debug',
        'function', 'class', 'module', 'import', 'def ', 'const ', 'let '
    ]):
        deepseek_response = get_deepseek_response(user_input)
        if deepseek_response:
            return deepseek_response
    
    # Creative writing → Claude (if available)
    if CLAUDE_AVAILABLE and any(word in user_input_lower for word in [
        'write a story', 'write a poem', 'creative writing', 'compose',
        'long form', 'essay', 'article', 'blog post', 'narrative',
        'fiction', 'non-fiction', 'prose', 'screenplay'
    ]):
        claude_response = get_claude_response(user_input)
        if claude_response:
            return claude_response
    
    # Default: Main GPT-4 for everything else
    return get_llm_response(user_input, context)