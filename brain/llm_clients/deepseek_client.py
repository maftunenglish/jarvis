# brain/llm_clients/deepseek_client.py
try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False
    print("⚠️  Requests package not available. DeepSeek support disabled.")

from config.settings import settings

def get_deepseek_response(user_input: str) -> str:
    """
    Specialized for coding tasks using DeepSeek Coder.
    Returns None if API is not configured or package not installed.
    """
    if not REQUESTS_AVAILABLE:
        return None
        
    if not settings.DEEPSEEK_API_KEY:
        return None
        
    try:
        response = requests.post(
            'https://api.deepseek.com/v1/chat/completions',
            headers={'Authorization': f'Bearer {settings.DEEPSEEK_API_KEY}'},
            json={
                'model': 'deepseek-coder',
                'messages': [{'role': 'user', 'content': user_input}],
                'temperature': 0.1
            },
            timeout=10
        )
        return response.json()['choices'][0]['message']['content']
    except Exception as e:
        print(f"DeepSeek API error: {e}")
        return None