import requests
import json

# Test data
data = {
    "message": {
        "type": "voice-request",
        "text": "שלום מה איתך",
        "sampleRate": 24000
    }
}

# Test AWS Lambda endpoint
url = "https://3wik39wypl.execute-api.us-east-1.amazonaws.com/tts"

try:
    print("Testing AWS Lambda with Google Cloud TTS...")
    response = requests.post(url, json=data, timeout=30)
    print(f"Status: {response.status_code}")
    print(f"Content-Type: {response.headers.get('Content-Type')}")
    print(f"Content-Length: {len(response.content)} bytes")
    
    if response.status_code == 200:
        print("✅ SUCCESS! Google Cloud TTS working on Lambda")
        with open("aws_gcp_test.pcm", "wb") as f:
            f.write(response.content)
        print("Audio saved as aws_gcp_test.pcm")
    else:
        print(f"❌ Error: {response.text}")
        
except Exception as e:
    print(f"❌ Test failed: {e}")
