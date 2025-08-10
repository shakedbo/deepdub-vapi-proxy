#!/usr/bin/env python3
"""
Quick test script for the optimized TTS proxy
"""

import requests
import json
import time

# Test configuration
BASE_URL = "http://localhost:5000"  # Change to your Render URL when deployed
VAPI_SECRET = "deepdub-secret-2025"  # Change to your actual secret

def test_health():
    """Test basic health endpoint"""
    print("🔍 Testing health endpoint...")
    try:
        response = requests.get(f"{BASE_URL}/")
        print(f"✅ Health check: {response.status_code} - {response.text}")
        return True
    except Exception as e:
        print(f"❌ Health check failed: {e}")
        return False

def test_stats():
    """Test performance stats endpoint"""
    print("📊 Testing stats endpoint...")
    try:
        response = requests.get(f"{BASE_URL}/stats")
        if response.status_code == 200:
            stats = response.json()
            print("✅ Stats endpoint working:")
            print(f"   Libraries: {stats.get('libraries', {})}")
            if 'audio_conversion' in stats:
                conv = stats['audio_conversion']
                print(f"   Conversions: {conv.get('total_conversions', 0)}")
                print(f"   Avg time: {conv.get('average_time_ms', 0)}ms")
            return True
        else:
            print(f"❌ Stats failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Stats test failed: {e}")
        return False

def test_tts():
    """Test TTS conversion"""
    print("🎤 Testing TTS conversion...")
    
    payload = {
        "message": {
            "type": "voice-request",
            "text": "שלום, זה בדיקה של המערכת החדשה",
            "sampleRate": 8000
        }
    }
    
    headers = {
        "Content-Type": "application/json",
        "X-VAPI-SECRET": VAPI_SECRET
    }
    
    try:
        start_time = time.time()
        response = requests.post(f"{BASE_URL}/tts", json=payload, headers=headers)
        end_time = time.time()
        
        if response.status_code == 200:
            duration = (end_time - start_time) * 1000
            content_length = len(response.content)
            print(f"✅ TTS success: {content_length} bytes in {duration:.1f}ms")
            print(f"   Content-Type: {response.headers.get('content-type', 'unknown')}")
            return True
        else:
            print(f"❌ TTS failed: {response.status_code}")
            try:
                error_data = response.json()
                print(f"   Error: {error_data.get('error', 'Unknown error')}")
            except:
                print(f"   Response: {response.text[:200]}")
            return False
    except Exception as e:
        print(f"❌ TTS test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("🚀 Testing Optimized Deepdub TTS Proxy")
    print("=" * 50)
    
    success_count = 0
    
    if test_health():
        success_count += 1
    
    print()
    if test_stats():
        success_count += 1
    
    print()
    if test_tts():
        success_count += 1
    
    print()
    print("=" * 50)
    print(f"📋 Results: {success_count}/3 tests passed")
    
    if success_count == 3:
        print("🎉 All tests passed! Server is ready for deployment.")
        
        # Get final stats
        try:
            response = requests.get(f"{BASE_URL}/stats")
            if response.status_code == 200:
                stats = response.json()
                if 'audio_conversion' in stats:
                    conv = stats['audio_conversion']
                    print(f"📊 Final performance: {conv.get('average_time_ms', 0):.1f}ms average conversion time")
        except:
            pass
            
    else:
        print("⚠️  Some tests failed. Check the configuration and try again.")

if __name__ == "__main__":
    main()
