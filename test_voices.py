#!/usr/bin/env python3
"""
Test Hebrew male voices and generate audio samples
"""

import os
import json
import requests
from dotenv import load_dotenv

load_dotenv()

def test_voice(voice_name, text="שלום, איך שלומך? זה קול של גבר בעברית."):
    """Test a specific voice by calling our local TTS service"""
    url = "http://localhost:5000/tts"
    
    # Test data
    test_data = {
        "text": text,
        "voice_name": voice_name
    }
    
    try:
        print(f"\nTesting voice: {voice_name}")
        print(f"Text: {text}")
        
        response = requests.post(url, json=test_data, timeout=30)
        
        if response.status_code == 200:
            # Save the audio file
            filename = f"test_voice_{voice_name.replace('-', '_')}.pcm"
            with open(filename, 'wb') as f:
                f.write(response.content)
            print(f"✓ Audio saved as: {filename}")
            print(f"  Size: {len(response.content)} bytes")
            return True
        else:
            print(f"✗ Error: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        print(f"✗ Error testing voice {voice_name}: {e}")
        return False

def main():
    print("🎙️  Testing Hebrew Male Voices")
    print("=" * 50)
    
    # Hebrew male voices (from best to good)
    male_voices = [
        "he-IL-Wavenet-B",    # Usually the best quality (neural)
        "he-IL-Wavenet-D",    # Also high quality (neural)  
        "he-IL-Standard-B",   # Good quality (standard)
        "he-IL-Standard-D"    # Good quality (standard)
    ]
    
    # Test text in Hebrew
    test_text = "שלום, אני שירות הקראה של טקסט. איך שלומך היום?"
    
    print(f"Test text: {test_text}")
    print()
    
    success_count = 0
    for voice in male_voices:
        if test_voice(voice, test_text):
            success_count += 1
    
    print(f"\n📊 Results: {success_count}/{len(male_voices)} voices tested successfully")
    
    if success_count > 0:
        print("\n🔧 Voice Quality Recommendations:")
        print("  1. he-IL-Wavenet-B - Best quality (WaveNet neural)")
        print("  2. he-IL-Wavenet-D - High quality (WaveNet neural)")  
        print("  3. he-IL-Standard-B - Good quality (Standard)")
        print("  4. he-IL-Standard-D - Good quality (Standard)")
        
        print("\n💡 To change voice, update your .env file:")
        print("     VOICE_NAME=he-IL-Wavenet-B")
        
        print("\n🎧 Listen to the generated .pcm files to choose your preferred voice")
        print("   You can convert PCM to WAV for easier playback:")
        print("   ffmpeg -f s16le -ar 24000 -ac 1 -i test_voice_he_IL_Wavenet_B.pcm output.wav")

if __name__ == "__main__":
    main()
