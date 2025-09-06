# test_groq.py
from groq_ai import GroqAI

def test_groq_integration():
    print("Testing Groq API integration...")
    
    # Initialize Groq
    try:
        groq = GroqAI()
        print("✅ Groq AI initialized successfully!")
    except Exception as e:
        print(f"❌ Error initializing Groq: {e}")
        return
    
    # Test single query
    print("\n1. Testing simple query...")
    response = groq.get_response("Explain quantum computing simply")
    print("Response:", response)
    
    # Test with system prompt
    print("\n2. Testing with system prompt...")
    response = groq.get_response(
        "How do I make pasta?",
        system_prompt="You are a chef assistant. Provide detailed cooking instructions."
    )
    print("Response:", response)
    
    # Test available models
    print("\n3. Available models:")
    models = groq.get_available_models()
    for model in models:
        print(f"   - {model}")
    
    print("\n✅ All tests completed successfully!")

if __name__ == "__main__":
    test_groq_integration()