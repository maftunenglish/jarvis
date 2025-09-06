# brain/utils/config_loader.py
import yaml
import os
import random
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime

class ConfigLoader:
    def __init__(self, config_path: str = "jarvis.yaml"):
        self.config_path = Path(config_path)
        self.config = self._load_config()
    
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from YAML file"""
        if not self.config_path.exists():
            print(f"⚠️ Config file {self.config_path} not found. Using defaults.")
            return self._get_default_config()
        
        try:
            with open(self.config_path, 'r', encoding='utf-8') as file:
                return yaml.safe_load(file) or {}
        except Exception as e:
            print(f"❌ Error loading config: {e}")
            return self._get_default_config()
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Return default configuration if YAML file is missing"""
        return {
            "personality": {
                "name": "J.A.R.V.I.S.",
                "role": "AI Assistant",
                "tone": "formal, professional",
                "style": "British politeness"
            },
            "behavior": {
                "greeting": "Good day, Sir. How may I assist you?",
                "error_response": "My apologies, Sir. A minor complication has occurred.",
                "unknown_response": "I'm not certain how to assist with that, Sir."
            },
            "system_prompt": "You are J.A.R.V.I.S., an AI assistant. Be professional and helpful."
        }
    
    def get_system_prompt(self) -> str:
        """Get the complete system prompt from config"""
        if "system_prompt" in self.config:
            return self.config["system_prompt"]
        
        # Build system prompt from personality config
        personality = self.config.get("personality", {})
        
        prompt_parts = [
            f"You are {personality.get('name', 'J.A.R.V.I.S.')}, {personality.get('role', 'an AI assistant')}.",
            f"Your tone should be {personality.get('tone', 'formal and professional')}.",
            f"Your style is {personality.get('style', 'British politeness')}.",
        ]
        
        if "knowledge" in self.config:
            knowledge = self.config["knowledge"]
            if "expertise" in knowledge:
                prompt_parts.append(f"You excel at: {', '.join(knowledge['expertise'])}.")
            if "avoid_topics" in knowledge:
                prompt_parts.append(f"Avoid discussing: {', '.join(knowledge['avoid_topics'])}.")
            if "specialities" in knowledge:
                prompt_parts.append(f"Specialities include: {', '.join(knowledge['specialities'])}.")
        
        return " ".join(prompt_parts)
    
    def get_greeting(self) -> str:
        """Get appropriate greeting based on time of day"""
        behavior = self.config.get("behavior", {})
        greeting = behavior.get("greeting", "")
        
        # If greeting is a multi-line string with time-based greetings
        if isinstance(greeting, str) and "Morning:" in greeting and "Afternoon:" in greeting and "Evening:" in greeting:
            current_hour = datetime.now().hour
            
            if 5 <= current_hour < 12:
                # Extract morning greeting
                lines = greeting.split('\n')
                for line in lines:
                    if line.strip().startswith('Morning:'):
                        return line.split('Morning:', 1)[1].strip()
            elif 12 <= current_hour < 17:
                # Extract afternoon greeting
                lines = greeting.split('\n')
                for line in lines:
                    if line.strip().startswith('Afternoon:'):
                        return line.split('Afternoon:', 1)[1].strip()
            else:
                # Extract evening greeting
                lines = greeting.split('\n')
                for line in lines:
                    if line.strip().startswith('Evening:'):
                        return line.split('Evening:', 1)[1].strip()
        
        return greeting
    
    def get_error_response(self) -> str:
        """Get error response"""
        return self.config.get("behavior", {}).get("error_response", "My apologies, Sir. An error occurred.")
    
    def get_unknown_response(self) -> str:
        """Get unknown query response"""
        return self.config.get("behavior", {}).get("unknown_response", "I'm not certain about that, Sir.")
    
    def get_thanks_response(self) -> str:
        """Get random thanks response"""
        behavior = self.config.get("behavior", {})
        thanks_responses = behavior.get("thanks_response", "")
        
        if isinstance(thanks_responses, str) and '\n' in thanks_responses:
            # Multi-line response, split and choose randomly
            responses = [line.strip() for line in thanks_responses.split('\n') if line.strip()]
            if responses:
                return random.choice(responses)
        
        return thanks_responses or "The pleasure is mine, Sir."
    
    def get_frustration_response(self) -> str:
        """Get random frustration response"""
        behavior = self.config.get("behavior", {})
        frustration_responses = behavior.get("frustration_response", "")
        
        if isinstance(frustration_responses, str) and '\n' in frustration_responses:
            responses = [line.strip() for line in frustration_responses.split('\n') if line.strip()]
            if responses:
                return random.choice(responses)
        
        return frustration_responses or "I detect elevated stress levels, Sir. Perhaps a moment's pause?"
    
    def get_completion_response(self) -> str:
        """Get random task completion response"""
        behavior = self.config.get("behavior", {})
        completion_responses = behavior.get("completion_response", "")
        
        if isinstance(completion_responses, str) and '\n' in completion_responses:
            responses = [line.strip() for line in completion_responses.split('\n') if line.strip()]
            if responses:
                return random.choice(responses)
        
        return completion_responses or "Task completed, Sir."
    
    def should_use_emojis(self) -> bool:
        """Check if emojis should be used"""
        return self.config.get("preferences", {}).get("use_emojis", False)
    
    def should_include_suggestions(self) -> bool:
        """Check if suggestions should be included"""
        return self.config.get("preferences", {}).get("include_suggestions", True)
    
    def should_be_proactive(self) -> bool:
        """Check if proactive behavior is enabled"""
        return self.config.get("preferences", {}).get("be_proactive", False)
    
    def get_user_address(self) -> str:
        """Get how to address the user"""
        return self.config.get("preferences", {}).get("address_user_as", "Sir")
    
    def get_expertise(self) -> List[str]:
        """Get areas of expertise"""
        return self.config.get("knowledge", {}).get("expertise", [])
    
    def get_avoid_topics(self) -> List[str]:
        """Get topics to avoid"""
        return self.config.get("knowledge", {}).get("avoid_topics", [])
    
    def get_specialities(self) -> List[str]:
        """Get specialities"""
        return self.config.get("knowledge", {}).get("specialities", [])
    
    def get_property(self, path: str, default: Any = None) -> Any:
        """Get a nested property from config using dot notation"""
        keys = path.split('.')
        value = self.config
        
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return default
        
        return value
    
    def get_personality_traits(self) -> Dict[str, Any]:
        """Get all personality traits"""
        return self.config.get("personality", {})
    
    def get_response_style_guidelines(self) -> List[str]:
        """Extract response guidelines from system prompt"""
        system_prompt = self.get_system_prompt()
        guidelines = []
        
        # Extract guidelines from system prompt
        lines = system_prompt.split('\n')
        for line in lines:
            if line.strip().startswith('-') or line.strip().startswith('•'):
                guidelines.append(line.strip())
        
        return guidelines

# Singleton instance
config_loader = ConfigLoader()