# debug_env.py
import os
from dotenv import load_dotenv

print("=== ENVIRONMENT DEBUG ===")
print("Current working directory:", os.getcwd())

# Try loading .env
load_dotenv()

# Check if .env file exists
env_exists = os.path.exists('.env')
print(".env file exists:", env_exists)

# Check all environment variables
print("\nAll environment variables containing 'GROQ':")
for key, value in os.environ.items():
    if 'GROQ' in key.upper():
        print(f"  {key}: {value}")

# Specific check
api_key = os.getenv("GROQ_API_KEY")
print(f"\nGROQ_API_KEY value: {'✅ SET' if api_key else '❌ NOT SET'}")
if api_key:
    print(f"Key length: {len(api_key)} characters")
    print(f"Key starts with: {api_key[:10]}...")