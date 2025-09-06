# quick_test.py
"""
Quick test script to verify:
1. API keys import from .env
2. Keys visible in api_manager
3. OpenAIClient works
"""

from brain.api_manager import api_manager
from brain.llm_clients.openai_client import OpenAIClient

def main():
    print("=== Quick Test: API Manager & OpenAI Client ===")

    # 1. Import keys from .env
    try:
        count = api_manager.import_keys_from_env()
        print(f"[1] Imported {count} key(s) from .env")
    except Exception as e:
        print(f"[1] Error importing from .env: {e}")

    # 2. List DB keys (unmasked if available)
    try:
        if hasattr(api_manager, "get_unmasked_keys"):
            db_keys = api_manager.get_unmasked_keys("openai")
            print(f"[2] DB contains {len(db_keys)} unmasked key(s).")
            for k in db_keys:
                print(f"    - Priority {k['priority']}: {k['api_key']}")
        else:
            print("[2] api_manager.get_unmasked_keys not available.")
            db_keys = []
    except Exception as e:
        print(f"[2] Error fetching unmasked keys: {e}")
        db_keys = []

    # 3. Create client & sync keys
    client = OpenAIClient(model="gpt-3.5-turbo")
    if db_keys:
        client.set_keys(db_keys)
        print(f"[3] Synced {len(db_keys)} key(s) into client.")
    else:
        print("[3] No keys to sync into client.")

    # 4. Run a sample completion
    try:
        print("[4] Sending test message to OpenAI...")
        resp = client.chat_completion(
            messages=[{"role": "user", "content": "Hello, reply with only the word 'pong'"}]
        )
        print("AI Response:", resp)
    except Exception as e:
        print(f"[4] Error during chat completion: {e}")

    print("=== Test Complete ===")

if __name__ == "__main__":
    main()
