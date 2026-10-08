import edge_tts
import asyncio
import os
import pygame
import re
import random

# Base configuration for JARVIS voice
VOICE = "en-US-AndrewMultilingualNeural" # Deep, natural, and authoritative
RATE = "+5%"
PITCH = "-15Hz" # Deep pitch for the 'Clyde' feel

# Use relative path for storage
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTPUT_FILE = os.path.join(BASE_DIR, "Data", "speech.mp3")

SPEECH_CALLBACK = None

def set_speech_callback(callback):
    global SPEECH_CALLBACK
    SPEECH_CALLBACK = callback

async def NeuralSpeak(Text):
    if not Text.strip():
        return

    # Clean text
    text_to_speak = Text.replace("...", ", ").replace(".", ". ")

    try:
        # Step 1: Generate Audio using edge-tts
        os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
        
        # Communicate using the specified parameters
        communicate = edge_tts.Communicate(text_to_speak, VOICE, rate=RATE, pitch=PITCH)
        await communicate.save(OUTPUT_FILE)
        
        # Check if file exists and has content
        if not os.path.exists(OUTPUT_FILE) or os.path.getsize(OUTPUT_FILE) == 0:
            print("TTS Error: Audio file was not generated.")
            return

        # Step 2: Play Audio
        if not pygame.mixer.get_init():
            pygame.mixer.init()

        pygame.mixer.music.load(OUTPUT_FILE)

        # Trigger GUI spike visualizer JUST before playback begins
        if SPEECH_CALLBACK:
            try:
                SPEECH_CALLBACK(OUTPUT_FILE)
            except Exception as cb_err:
                print(f"Speech callback error: {cb_err}")

        pygame.mixer.music.play()

        while pygame.mixer.music.get_busy():
            await asyncio.sleep(0.1)

        try:
            pygame.mixer.music.stop()
            pygame.mixer.music.unload()
        except Exception:
            pass
        
    except Exception as e:
        print(f"TTS Error: {e}")


def Speak(Text):
    """Sync wrapper for startup calls."""
    try:
        # Try to use current loop or create new one
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
        if loop.is_running():
            asyncio.run_coroutine_threadsafe(NeuralSpeak(Text), loop)
        else:
            loop.run_until_complete(NeuralSpeak(Text))
    except Exception as e:
        print(f"Speak Wrapper Error: {e}")

if __name__ == "__main__":
    # Test
    asyncio.run(NeuralSpeak("Hello. I am JARVIS. I have successfully integrated the premium neural voice profile. My responses now include natural micro-pauses and breathing patterns, just as you requested."))
