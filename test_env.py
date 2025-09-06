# test_env.py
import os
from dotenv import load_dotenv

print("Current directory:", os.getcwd())
print("Files in directory:", os.listdir('.'))

# Load environment
load_dotenv()

# Check if keys are loaded
print("OPENAI_API_KEY_1:", os.getenv("OPENAI_API_KEY_1"))
print("OPENAI_API_KEY:", os.getenv("OPENAI_API_KEY"))
print("All environment variables:", dict(os.environ))