"""
DeepSeek AI client implementation.
"""
import os
import requests
from typing import List, Dict, Any

class DeepSeekClient:
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv("DEEPSEEK_API_KEY")
        self.base_url = "https://api.deepseek.com/v1/chat/completions"
        
    def chat_completion(self, messages: List[Dict[str, Any]], **kwargs) -> Dict[str, Any]:
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": "deepseek-chat",
            "messages": messages,
            "stream": False,
            **kwargs
        }
        
        response = requests.post(self.base_url, json=payload, headers=headers)
        response.raise_for_status()
        return response.json()
    
    def say(self, text: str, **kwargs) -> str:
        messages = [{"role": "user", "content": text}]
        resp = self.chat_completion(messages=messages, **kwargs)
        return resp["choices"][0]["message"]["content"]

# Compatibility function
def get_deepseek_response(user_input: str, context: list = None) -> str:
    client = DeepSeekClient()
    
    messages = []
    if context:
        for exchange in context[-3:]:
            messages.append({"role": "user", "content": exchange.get('user', '')})
            messages.append({"role": "assistant", "content": exchange.get('ai', '')})
    
    messages.append({"role": "user", "content": user_input})
    
    try:
        response = client.chat_completion(messages=messages)
        return response["choices"][0]["message"]["content"]
    except Exception as e:
        return f"Error: {str(e)}"