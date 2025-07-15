import requests
import json
import time

def test_lambda_endpoint():
    url = "https://3wik39wypl.execute-api.us-east-1.amazonaws.com/tts"
    
    # Test 1: Simple text
    print("=== Test 1: Simple text (demo mode) ===")
    try:
        data = {"text": "Hello world"}
        response = requests.post(url, json=data, timeout=15)
        print(f"Status: {response.status_code}")
        print(f"Headers: {dict(response.headers)}")
        print(f"Response length: {len(response.content)} bytes")
        if response.status_code != 200:
            print(f"Error response: {response.text}")
        else:
            print("✅ Simple test passed!")
    except Exception as e:
        print(f"❌ Simple test failed: {e}")
    
    print("\n" + "="*50 + "\n")
    
    # Test 2: VAPI format
    print("=== Test 2: VAPI format ===")
    try:
        data = {
            "message": {
                "type": "voice-request",
                "text": "Test Hebrew text",
                "sampleRate": 24000
            }
        }
        response = requests.post(url, json=data, timeout=15)
        print(f"Status: {response.status_code}")
        print(f"Headers: {dict(response.headers)}")
        print(f"Response length: {len(response.content)} bytes")
        if response.status_code != 200:
            print(f"Error response: {response.text}")
        else:
            print("✅ VAPI test passed!")
    except Exception as e:
        print(f"❌ VAPI test failed: {e}")

if __name__ == "__main__":
    print("🧪 Lambda Diagnostic Test")
    test_lambda_endpoint()
    print("\n🏁 Tests completed")
