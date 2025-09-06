"""
Google Gemini AI client implementation.
"""
import os
import google.generativeai as genai
from typing import List, Dict, Any

class GeminiClient:
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        if self.api_key:
            genai.configure(api_key=self.api_key)
        self.model = "gemini-1.0-pro"
        
    def chat_completion(self, messages: List[Dict[str, Any]], **kwargs) -> Dict[str, Any]:
        if not self.api_key:
            raise ValueError("Gemini API key not configured")
        
        # Convert messages to Gemini format
        gemini_messages = []
        for msg in messages:
            if msg["role"] == "user":
                gemini_messages.append({"role": "user", "parts": [msg["content"]]})
            elif msg["role"] == "assistant":
                gemini_messages.append({"role": "model", "parts": [msg["content"]]})
        
        # Start chat session
        model = genai.GenerativeModel(self.model)
        chat = model.start_chat(history=gemini_messages[:-1])  # All but last message
        
        # Send latest message
        response = chat.send_message(messages[-1]["content"])
        return {"choices": [{"message": {"content": response.text}}]}
    
    def say(self, text: str, **kwargs) -> str:
        messages = [{"role": "user", "content": text}]
        resp = self.chat_completion(messages=messages, **kwargs)
        return resp["choices"][0]["message"]["content"]

# Compatibility function
def get_gemini_response(user_input: str, context: list = None) -> str:
    client = GeminiClient()
    
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