#!/usr/bin/env python3
"""
Test script to debug ElevenLabs API issues following official documentation
"""

import os
from dotenv import load_dotenv
from elevenlabs import ElevenLabs

# Load environment variables
load_dotenv()

# Configuration
ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")
ELEVENLABS_VOICE_ID = os.getenv("ELEVENLABS_VOICE_ID")
ELEVENLABS_MODEL_ID = os.getenv("ELEVENLABS_MODEL_ID")

print("=== ElevenLabs API Test (Official Pattern) ===")
print(f"API Key: {ELEVENLABS_API_KEY[:10]}..." if ELEVENLABS_API_KEY else "No API Key")
print(f"Voice ID: {ELEVENLABS_VOICE_ID}")
print(f"Model ID: {ELEVENLABS_MODEL_ID}")

if not ELEVENLABS_API_KEY:
    print("ERROR: ELEVENLABS_API_KEY not set in environment")
    exit(1)

if not ELEVENLABS_VOICE_ID:
    print("ERROR: ELEVENLABS_VOICE_ID not set in environment")
    exit(1)

# Initialize ElevenLabs client following official documentation
client = ElevenLabs(api_key=ELEVENLABS_API_KEY)

# Test text (Hebrew)
test_text = "שלום עולם, זהו מבחן של המערכת."

print(f"\nTesting ElevenLabs API with Hebrew text: '{test_text}'")

try:
    # Generate audio following official example pattern for v2+ SDK
    audio = client.text_to_speech.convert(
        text=test_text,
        voice_id=ELEVENLABS_VOICE_ID,
        model_id=ELEVENLABS_MODEL_ID,
        output_format="pcm_16000"  # PCM format for VAPI
    )
    
    # Convert audio generator to bytes (following official example)
    audio_bytes = b"".join(audio)
    
    print(f"✅ SUCCESS! Generated {len(audio_bytes)} bytes of PCM audio")
    print("🎉 Perfect for VAPI integration - no conversion needed!")
    
    # Save to file for testing
    with open("test_output_official.pcm", "wb") as f:
        f.write(audio_bytes)
    print("Audio saved to test_output_official.pcm")
    
except Exception as e:
    error_msg = str(e)
    print(f"❌ Error: {error_msg}")
    
    if "model_access_denied" in error_msg:
        print("\n📞 Contact ElevenLabs for v3 access:")
        print("   Email: sales@elevenlabs.io")
        print("   Subject: Request access to eleven_v3 for Hebrew TTS")
    
    exit(1)
