# interfaces/voice_input.py
import speech_recognition as sr

def listen_for_command():
    """
    Listens for and transcribes audio input from the microphone.
    
    Returns:
        str: The transcribed text, or None if no audio was understood.
    """
    recognizer = sr.Recognizer()
    
    with sr.Microphone() as source:
        print("🎙️  Listening...")
        # Adjust for ambient noise
        recognizer.adjust_for_ambient_noise(source, duration=0.5)
        
        try:
            # Listen for audio input
            audio = recognizer.listen(source, timeout=5, phrase_time_limit=10)
            print("Processing audio...")
            
            # Convert speech to text
            text = recognizer.recognize_google(audio)
            print(f"You said: {text}")
            return text.lower()
            
        except sr.WaitTimeoutError:
            print("No speech detected within the timeout period.")
            return None
        except sr.UnknownValueError:
            print("Could not understand the audio.")
            return None
        except Exception as e:
            print(f"An error occurred: {e}")
            return None