# interfaces/voice_output.py
import pyttsx3

# Initialize the TTS engine once
engine = pyttsx3.init()

# Configure voice properties (optional)
voices = engine.getProperty('voices')
if voices:
    engine.setProperty('voice', voices[1].id)  # Typically index 1 is a female voice
engine.setProperty('rate', 180)  # Speech speed

def speak(text):
    """
    Converts text to speech and plays it aloud.
    
    Args:
        text (str): The text to be spoken.
    """
    try:
        print(f"AI: {text}")  # Also print to console
        engine.say(text)
        engine.runAndWait()
    except Exception as e:
        print(f"Error in speech synthesis: {e}")