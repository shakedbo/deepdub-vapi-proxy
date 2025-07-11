#!/usr/bin/env python3
"""
Test script to debug ElevenLabs API issues
"""

import os
import requests
from dotenv import load_dotenv
from elevenlabs import ElevenLabs

# Load environment variables
load_dotenv()

# Configuration
ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")
ELEVENLABS_VOICE_ID = os.getenv("ELEVENLABS_VOICE_ID")
ELEVENLABS_MODEL_ID = os.getenv("ELEVENLABS_MODEL_ID", "eleven_multilingual_v2")

print("=== ElevenLabs API Test ===")
print(f"API Key: {ELEVENLABS_API_KEY[:10]}..." if ELEVENLABS_API_KEY else "No API Key")
print(f"Voice ID: {ELEVENLABS_VOICE_ID}")
print(f"Model ID: {ELEVENLABS_MODEL_ID}")

if not ELEVENLABS_API_KEY:
    print("ERROR: ELEVENLABS_API_KEY not set in environment")
    exit(1)

if not ELEVENLABS_VOICE_ID:
    print("ERROR: ELEVENLABS_VOICE_ID not set in environment")
    exit(1)

# Initialize ElevenLabs client
client = ElevenLabs(api_key=ELEVENLABS_API_KEY)

# Test text
test_text = "שלום עולם, זהו מבחן של המערכת."

print(f"\nTesting ElevenLabs API with text: '{test_text}'")

try:
    # Generate audio
    audio_data = client.text_to_speech.convert(
        voice_id=ELEVENLABS_VOICE_ID,
        text=test_text,
        model_id=ELEVENLABS_MODEL_ID
    )
    
    # Convert iterator to bytes
    audio_bytes = b''.join(audio_data)
    
    print(f"✅ Success! Generated {len(audio_bytes)} bytes of audio")
    
    # Save to file for testing
    with open("test_output.mp3", "wb") as f:
        f.write(audio_bytes)
    print("Audio saved to test_output.mp3")
    
except Exception as e:
    print(f"❌ Error: {e}")
    exit(1)
