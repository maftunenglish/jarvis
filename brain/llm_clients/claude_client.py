# brain/llm_clients/claude_client.py
try:
    import anthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False
    print("⚠️  Anthropic package not installed. Claude support disabled.")

from config.settings import settings

def get_claude_response(user_input: str) -> str:
    """
    Specialized for creative writing and long-form content using Claude.
    Returns None if API is not configured or package not installed.
    """
    if not ANTHROPIC_AVAILABLE:
        return None
        
    if not settings.ANTHROPIC_API_KEY:
        return None
        
    try:
        client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)
        
        response = client.messages.create(
            model="claude-3-sonnet-20240229",
            max_tokens=1000,
            messages=[{"role": "user", "content": user_input}]
        )
        
        return response.content[0].text
    except Exception as e:
        print(f"Claude API error: {e}")
        return None