# groq_ai.py
import os
import time
from typing import Optional, List, Dict, Any
from groq import Groq
from dotenv import load_dotenv
from pathlib import Path
import json

class GroqAI:
    def __init__(self, api_key: Optional[str] = None, model: str = "llama-3.1-8b-instant"):
        """
        Complete Groq AI integration for Jarvis
        """
        # Load environment variables
        try:
            possible_paths = [Path('.env'), Path(__file__).parent / '.env']
            for env_path in possible_paths:
                if env_path.exists():
                    load_dotenv(env_path)
                    break
            else:
                load_dotenv()
        except:
            pass
        
        self.api_key = api_key or os.getenv("GROQ_API_KEY")
        
        if not self.api_key:
            raise ValueError("Groq API key is required. Set GROQ_API_KEY in .env file")
        
        # Initialize Groq client
        self.client = Groq(api_key=self.api_key)
        self.model = model
        self.conversation_history = []
        self.max_history_length = 6  # Keep last 3 exchanges
        
        # Usage tracking
        self.usage_file = Path("groq_usage.json")
        self.usage_data = self._load_usage_data()
        self.daily_limit = 50
        self.monthly_limit = 500
        
        print(f"🤖 Groq AI initialized with model: {model}")
        print(f"📊 Usage: {self.usage_data['daily_requests']}/{self.daily_limit} today")
    
    def _load_usage_data(self) -> Dict:
        """Load usage data from file"""
        default_data = {
            "total_requests": 0,
            "daily_requests": 0,
            "monthly_requests": 0,
            "last_reset_date": time.strftime("%Y-%m-%d"),
            "last_reset_month": time.strftime("%Y-%m"),
            "model_usage": {}
        }
        
        try:
            if self.usage_file.exists():
                with open(self.usage_file, 'r') as f:
                    return json.load(f)
        except:
            pass
        
        return default_data
    
    def _save_usage_data(self):
        """Save usage data to file"""
        try:
            with open(self.usage_file, 'w') as f:
                json.dump(self.usage_data, f, indent=2)
        except:
            pass
    
    def _check_usage_limits(self) -> bool:
        """Check if usage is within limits"""
        current_date = time.strftime("%Y-%m-%d")
        current_month = time.strftime("%Y-%m")
        
        # Reset counters if new day/month
        if current_date != self.usage_data["last_reset_date"]:
            self.usage_data["daily_requests"] = 0
            self.usage_data["last_reset_date"] = current_date
        
        if current_month != self.usage_data["last_reset_month"]:
            self.usage_data["monthly_requests"] = 0
            self.usage_data["last_reset_month"] = current_month
        
        # Check limits
        if self.usage_data["daily_requests"] >= self.daily_limit:
            return False, "Daily limit reached"
        
        if self.usage_data["monthly_requests"] >= self.monthly_limit:
            return False, "Monthly limit reached"
        
        return True, ""
    
    def get_response(self, 
                    prompt: str, 
                    system_prompt: Optional[str] = None, 
                    max_tokens: int = 400,
                    temperature: float = 0.7,
                    use_history: bool = True) -> str:
        """
        Get response from Groq AI with usage tracking
        """
        # Check usage limits
        can_proceed, reason = self._check_usage_limits()
        if not can_proceed:
            return f"⚠️ {reason}. Please try again later."
        
        try:
            messages = []
            
            # System prompt
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt[:400]})
            
            # Conversation history
            if use_history and self.conversation_history:
                for role, content in self.conversation_history:
                    messages.append({"role": role, "content": content[:200]})
            
            # Current message
            messages.append({"role": "user", "content": prompt[:800]})
            
            # Update usage counters
            self.usage_data["total_requests"] += 1
            self.usage_data["daily_requests"] += 1
            self.usage_data["monthly_requests"] += 1
            
            # Track model usage
            if self.model not in self.usage_data["model_usage"]:
                self.usage_data["model_usage"][self.model] = 0
            self.usage_data["model_usage"][self.model] += 1
            
            self._save_usage_data()
            
            # API call
            start_time = time.time()
            completion = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                top_p=1,
                stream=False,
                timeout=20
            )
            
            response_time = time.time() - start_time
            response = completion.choices[0].message.content
            
            # Update history
            self._update_history("user", prompt[:150])
            self._update_history("assistant", response[:300])
            
            print(f"✅ Request {self.usage_data['daily_requests']}/{self.daily_limit} - {response_time:.1f}s")
            return response
            
        except Exception as e:
            # Rollback counters on error
            self.usage_data["total_requests"] = max(0, self.usage_data["total_requests"] - 1)
            self.usage_data["daily_requests"] = max(0, self.usage_data["daily_requests"] - 1)
            self.usage_data["monthly_requests"] = max(0, self.usage_data["monthly_requests"] - 1)
            self._save_usage_data()
            
            return f"❌ Error: {str(e)}"
    
    def _update_history(self, role: str, content: str):
        """Update conversation history"""
        self.conversation_history.append((role, content))
        if len(self.conversation_history) > self.max_history_length:
            self.conversation_history = self.conversation_history[-self.max_history_length:]
    
    def get_available_models(self) -> List[str]:
        """Get list of available models"""
        return [
            "llama-3.1-8b-instant",      # Fast general purpose
            "llama-3.1-70b-versatile",   # Powerful versatile
            "mixtral-8x7b-32768",        # Best for coding
            "gemma2-9b-it",              # Efficient balance
            "claude-3.5-sonnet-20240620" # Premium model
        ]
    
    def change_model(self, model_name: str) -> str:
        """Switch to a different model"""
        available_models = self.get_available_models()
        if model_name in available_models:
            old_model = self.model
            self.model = model_name
            return f"✅ Switched from {old_model} to {model_name}"
        else:
            return f"❌ Model not available. Choose from: {available_models}"
    
    def get_usage_stats(self) -> Dict:
        """Get detailed usage statistics"""
        return {
            "daily_used": self.usage_data["daily_requests"],
            "daily_limit": self.daily_limit,
            "daily_remaining": max(0, self.daily_limit - self.usage_data["daily_requests"]),
            "monthly_used": self.usage_data["monthly_requests"],
            "monthly_limit": self.monthly_limit,
            "monthly_remaining": max(0, self.monthly_limit - self.usage_data["monthly_requests"]),
            "total_requests": self.usage_data["total_requests"],
            "model_usage": self.usage_data["model_usage"]
        }
    
    def clear_history(self):
        """Clear conversation history"""
        self.conversation_history = []
        return "✅ Conversation history cleared"
    
    def reset_usage_limits(self, daily_limit: int = None, monthly_limit: int = None):
        """Adjust usage limits"""
        if daily_limit:
            self.daily_limit = daily_limit
        if monthly_limit:
            self.monthly_limit = monthly_limit
        return f"✅ Limits set: {self.daily_limit}/day, {self.monthly_limit}/month"