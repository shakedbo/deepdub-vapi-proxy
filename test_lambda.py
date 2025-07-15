import requests

# Test AWS Lambda endpoint
url = "https://3wik39wypl.execute-api.us-east-1.amazonaws.com/prod/tts"

print("Testing AWS Lambda with Google Cloud TTS...")

# Test 1: Simple Hebrew text
try:
    data = {"text": "שלום עולם"}
    response = requests.post(url, json=data, timeout=15)
    print(f"Status: {response.status_code}")
    print(f"Content-Type: {response.headers.get('Content-Type')}")
    print(f"Content-Length: {len(response.content)} bytes")
    
    if response.status_code == 200:
        print("✅ SUCCESS! Google Cloud TTS working on Lambda")
        with open("aws_test.pcm", "wb") as f:
            f.write(response.content)
        print("Audio saved as aws_test.pcm")
    else:
        print(f"❌ Error: {response.text}")
        
except Exception as e:
    print(f"❌ Test failed: {e}")

print("\n" + "="*50)

# Test 2: VAPI format
try:
    print("Testing VAPI format...")
    data = {
        "message": {
            "type": "voice-request",
            "text": "שלום מה איתך היום",
            "sampleRate": 24000
        }
    }
    response = requests.post(url, json=data, timeout=15)
    print(f"Status: {response.status_code}")
    print(f"Content-Type: {response.headers.get('Content-Type')}")
    print(f"Content-Length: {len(response.content)} bytes")
    
    if response.status_code == 200:
        print("✅ VAPI format working!")
        with open("aws_vapi_test.pcm", "wb") as f:
            f.write(response.content)
        print("Audio saved as aws_vapi_test.pcm")
    else:
        print(f"❌ Error: {response.text}")
        
except Exception as e:
    print(f"❌ VAPI test failed: {e}")

print("\n🏁 Tests completed")
