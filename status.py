# Quick test to see what keys you have
from brain.api_manager import api_manager
status = api_manager.get_key_status('openai')
print("Current keys:", status)