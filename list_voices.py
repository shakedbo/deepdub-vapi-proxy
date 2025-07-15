#!/usr/bin/env python3
"""
List available Hebrew voices from Google Cloud Text-to-Speech
"""

import os
from dotenv import load_dotenv
from google.cloud import texttospeech

load_dotenv()

def list_hebrew_voices():
    """List all available Hebrew voices"""
    try:
        # Initialize the client
        credentials_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
        if credentials_path and os.path.exists(credentials_path):
            client = texttospeech.TextToSpeechClient.from_service_account_file(credentials_path)
        else:
            client = texttospeech.TextToSpeechClient()
        
        # List all voices
        voices = client.list_voices()
        
        print("Available Hebrew (he-IL) voices:")
        print("=" * 50)
        
        hebrew_voices = []
        for voice in voices.voices:
            for language_code in voice.language_codes:
                if language_code.startswith('he-'):
                    hebrew_voices.append({
                        'name': voice.name,
                        'language': language_code,
                        'gender': voice.ssml_gender.name,
                        'natural_sample_rate': voice.natural_sample_rate_hertz
                    })
        
        # Sort by gender and name
        hebrew_voices.sort(key=lambda x: (x['gender'], x['name']))
        
        current_gender = None
        for voice in hebrew_voices:
            if voice['gender'] != current_gender:
                current_gender = voice['gender']
                print(f"\n{current_gender} voices:")
                print("-" * 20)
            
            print(f"  Name: {voice['name']}")
            print(f"  Language: {voice['language']}")
            print(f"  Sample Rate: {voice['natural_sample_rate']} Hz")
            print()
        
        # Show male voices specifically
        male_voices = [v for v in hebrew_voices if v['gender'] == 'MALE']
        if male_voices:
            print("\n🎙️  MALE HEBREW VOICES (Recommended):")
            print("=" * 50)
            for voice in male_voices:
                print(f"✓ {voice['name']} ({voice['language']}) - {voice['natural_sample_rate']} Hz")
        
        return hebrew_voices
        
    except Exception as e:
        print(f"Error listing voices: {e}")
        return []

if __name__ == "__main__":
    voices = list_hebrew_voices()
    
    if voices:
        print(f"\nFound {len(voices)} Hebrew voices total")
        male_count = len([v for v in voices if v['gender'] == 'MALE'])
        female_count = len([v for v in voices if v['gender'] == 'FEMALE'])
        print(f"Male voices: {male_count}")
        print(f"Female voices: {female_count}")
    else:
        print("No voices found or error occurred")
