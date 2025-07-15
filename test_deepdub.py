"""
Test script for Deepdub TTS proxy with VAPI format
"""
import requests
import json

def test_vapi_format():
    """Test with VAPI message format"""
    print("Testing VAPI format...")
    
    url = "http://localhost:5000/tts"
    
    # VAPI format as specified
    data = {
        "message": {
            "type": "voice-request",
            "text": "שלום מה איתך היום איך אתה מרגיש?",  # Hebrew text from your example
            "sampleRate": 24000
        }
    }
    
    try:
        response = requests.post(url, json=data)
        print(f"Status: {response.status_code}")
        print(f"Content-Type: {response.headers.get('Content-Type')}")
        print(f"Content-Length: {len(response.content)} bytes")
        
        if response.status_code == 200:
            # Save the audio file for testing
            with open("test_output.pcm", "wb") as f:
                f.write(response.content)
            print("✅ Test successful! Audio saved as test_output.pcm")
            return True
        else:
            print(f"❌ Test failed: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Test error: {e}")
        return False

def test_simple_format():
    """Test with simple text format"""
    print("Testing simple format...")
    
    url = "http://localhost:5000/tts"
    data = {"text": "Hello, this is a test of the Deepdub TTS service."}
    
    try:
        response = requests.post(url, json=data)
        print(f"Status: {response.status_code}")
        print(f"Content-Type: {response.headers.get('Content-Type')}")
        print(f"Content-Length: {len(response.content)} bytes")
        
        if response.status_code == 200:
            print("✅ Simple format test successful!")
            return True
        else:
            print(f"❌ Test failed: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Test error: {e}")
        return False

def test_health():
    """Test health endpoint"""
    print("Testing health endpoint...")
    
    try:
        response = requests.get("http://localhost:5000/health")
        print(f"Status: {response.status_code}")
        print(f"Response: {response.json()}")
        return response.status_code == 200
    except Exception as e:
        print(f"❌ Health check error: {e}")
        return False

def test_aws_endpoint():
    """Test AWS Lambda endpoint"""
    print("Testing AWS Lambda endpoint...")
    
    url = "https://3wik39wypl.execute-api.us-east-1.amazonaws.com/tts"
    
    # VAPI format
    data = {
        "message": {
            "type": "voice-request", 
            "text": "שלום, זה בדיקה של שירות Deepdub",
            "sampleRate": 24000
        }
    }
    
    try:
        response = requests.post(url, json=data, timeout=30)
        print(f"Status: {response.status_code}")
        print(f"Content-Type: {response.headers.get('Content-Type')}")
        print(f"Content-Length: {len(response.content)} bytes")
        
        if response.status_code == 200:
            with open("aws_test_output.pcm", "wb") as f:
                f.write(response.content)
            print("✅ AWS test successful! Audio saved as aws_test_output.pcm")
            return True
        else:
            print(f"❌ AWS test failed: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ AWS test error: {e}")
        return False

if __name__ == "__main__":
    print("🧪 Testing Deepdub TTS Proxy\n")
    
    # Test health first
    if test_health():
        print("\n" + "="*50)
        # Test VAPI format
        test_vapi_format()
        
        print("\n" + "="*50)
        # Test simple format  
        test_simple_format()
        
        print("\n" + "="*50)
        # Test AWS endpoint
        test_aws_endpoint()
    
    print("\n✅ Tests completed!")
