#!/usr/bin/env python3
"""
Test script to debug Deepdub API issues
"""
import requests
import json
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

DEEPDUB_API_KEY = os.getenv("DEEPDUB_API_KEY")
VOICE_PROMPT_ID = os.getenv("DEEPDUB_VOICE_PROMPT_ID")

print("=== Deepdub API Test ===")
print(f"API Key: {DEEPDUB_API_KEY[:10]}..." if DEEPDUB_API_KEY else "No API Key")
print(f"Voice Prompt ID: {VOICE_PROMPT_ID}")

if not DEEPDUB_API_KEY:
    print("ERROR: No API key found!")
    exit(1)

if not VOICE_PROMPT_ID:
    print("ERROR: No voice prompt ID found!")
    exit(1)

# Test payload
payload = {
    "model": "dd-etts-1.1",
    "targetText": "שלום מה שלומך היום?",
    "locale": "he-IL",
    "voicePromptId": VOICE_PROMPT_ID
}

headers = {
    "Content-Type": "application/json",
    "x-api-key": DEEPDUB_API_KEY
}

print("\n=== Making API Request ===")
print(f"URL: https://restapi.deepdub.ai/tts")
print(f"Headers: {headers}")
print(f"Payload: {json.dumps(payload, ensure_ascii=False, indent=2)}")

try:
    response = requests.post(
        "https://restapi.deepdub.ai/tts",
        headers=headers,
        json=payload,
        timeout=30
    )
    
    print(f"\n=== Response ===")
    print(f"Status Code: {response.status_code}")
    print(f"Headers: {dict(response.headers)}")
    print(f"Content Length: {len(response.text)}")
    print(f"Raw Content: {response.text}")
    
    if response.status_code == 200:
        try:
            json_response = response.json()
            print(f"JSON Response: {json.dumps(json_response, indent=2)}")
            
            audio_url = json_response.get("audioUrl")
            if audio_url:
                print(f"Audio URL: {audio_url}")
                print("✅ SUCCESS: API call worked!")
            else:
                print("❌ ERROR: No audioUrl in response")
        except json.JSONDecodeError as e:
            print(f"❌ JSON Decode Error: {e}")
    else:
        print(f"❌ API Error: {response.status_code}")
        
except requests.exceptions.RequestException as e:
    print(f"❌ Request Error: {e}")
