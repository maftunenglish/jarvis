import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class Settings:
    """Application settings loaded from environment variables."""

    # OpenAI API Configuration
  
    DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
    ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
    # NewsAPI Configuration (for future use)
    NEWS_API_KEY = os.getenv("NEWS_API_KEY")
    
    # NEW: Multiple API keys support
    OPENAI_API_KEY_1 = os.getenv("OPENAI_API_KEY_1")
    OPENAI_API_KEY_2 = os.getenv("OPENAI_API_KEY_2")
    OPENAI_API_KEY_3 = os.getenv("OPENAI_API_KEY_3")
    OPENAI_API_KEY_4 = os.getenv("OPENAI_API_KEY_4")
    OPENAI_API_KEY_5 = os.getenv("OPENAI_API_KEY_5")
    # Add other configuration variables here as needed


# Create a settings instance that can be imported elsewhere
settings = Settings()
