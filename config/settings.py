import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Settings:
    """Application settings loaded from environment variables."""
    
    # OpenAI API Configuration
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
    
    # NewsAPI Configuration (for future use)
    NEWS_API_KEY = os.getenv('NEWS_API_KEY')
    
    # Add other configuration variables here as needed

# Create a settings instance that can be imported elsewhere
settings = Settings()