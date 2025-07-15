"""
Lightweight TTS Proxy for VAPI - Lambda version without grpc dependencies

Features:
- Supports Hebrew text-to-speech via REST API
- Returns native PCM audio format (LINEAR16)
- Compatible with VAPI requirements
- No grpc dependencies for Lambda compatibility
"""

import os
import io
import wave
import json
import base64
import math
import requests
from flask import Flask, request, Response, jsonify
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

# Environment variables
GOOGLE_CLOUD_CREDENTIALS_PATH = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
VOICE_NAME = os.getenv("VOICE_NAME", "he-IL-Wavenet-A")  # Hebrew voice
VOICE_LANGUAGE = os.getenv("VOICE_LANGUAGE", "he-IL")  # Hebrew locale
VAPI_SECRET = os.getenv("VAPI_SECRET", "deepdub-secret-2025")
DEMO_MODE = os.getenv("DEMO_MODE", "false").lower() == "true"

# Google Cloud TTS REST API endpoint
GOOGLE_TTS_API_URL = "https://texttospeech.googleapis.com/v1/text:synthesize"

def get_google_access_token():
    """Get access token for Google Cloud TTS using service account"""
    try:
        if GOOGLE_CLOUD_CREDENTIALS_PATH and os.path.exists(GOOGLE_CLOUD_CREDENTIALS_PATH):
            # Read service account key
            with open(GOOGLE_CLOUD_CREDENTIALS_PATH, 'r') as f:
                service_account = json.load(f)
            
            # Use Google Auth to get access token
            import google.auth.transport.requests
            import google.oauth2.service_account
            
            credentials = google.oauth2.service_account.Credentials.from_service_account_info(
                service_account,
                scopes=['https://www.googleapis.com/auth/cloud-platform']
            )
            
            # Get fresh token
            request = google.auth.transport.requests.Request()
            credentials.refresh(request)
            
            return credentials.token
        else:
            print("No credentials file found, using demo mode")
            return None
    except Exception as e:
        print(f"Error getting access token: {e}")
        return None

def call_google_tts_rest(text, sample_rate=24000):
    """Call Google Cloud TTS using REST API instead of grpc"""
    try:
        token = get_google_access_token()
        if not token:
            return None
        
        headers = {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        }
        
        payload = {
            'input': {'text': text},
            'voice': {
                'languageCode': VOICE_LANGUAGE,
                'name': VOICE_NAME
            },
            'audioConfig': {
                'audioEncoding': 'LINEAR16',
                'sampleRateHertz': sample_rate
            }
        }
        
        response = requests.post(GOOGLE_TTS_API_URL, headers=headers, json=payload)
        
        if response.status_code == 200:
            result = response.json()
            audio_content = base64.b64decode(result['audioContent'])
            print(f"Received audio from Google TTS REST API: {len(audio_content)} bytes")
            return audio_content
        else:
            print(f"Google TTS REST API error: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        print(f"Error calling Google TTS REST API: {e}")
        return None

def generate_demo_pcm(text, sample_rate=24000, duration_seconds=2):
    """Generate demo PCM audio for testing"""
    num_samples = int(sample_rate * duration_seconds)
    pcm_data = bytearray()
    
    for i in range(num_samples):
        # Generate a simple sine wave
        t = i / sample_rate
        frequency = 440  # A4 note
        amplitude = int(16383 * math.sin(2 * math.pi * frequency * t))
        pcm_data.extend(amplitude.to_bytes(2, byteorder='little', signed=True))
    
    return bytes(pcm_data)

def extract_pcm_from_wav(wav_data):
    """Extract raw PCM data from WAV file"""
    try:
        wav_io = io.BytesIO(wav_data)
        with wave.open(wav_io, 'rb') as wav_file:
            frames = wav_file.readframes(wav_file.getnframes())
            return frames
    except Exception as e:
        print(f"Error extracting PCM from WAV: {e}")
        return None

@app.route('/tts', methods=['POST'])
def tts():
    """Text-to-speech endpoint that returns PCM audio for VAPI"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No JSON data provided"}), 400
        
        # Handle VAPI format: {"message": {"type": "voice-request", "text": "...", "sampleRate": 24000}}
        if 'message' in data:
            message = data['message']
            text = message.get('text', '')
            sample_rate = message.get('sampleRate', 24000)
            print(f"VAPI format detected - text: '{text[:100]}{'...' if len(text) > 100 else ''}'")
            print(f"Requested sample rate: {sample_rate}")
        else:
            # Handle simple format: {"text": "..."}
            text = data.get('text', '')
            sample_rate = 24000  # Default for VAPI
            print(f"Simple format detected - text: '{text[:100]}{'...' if len(text) > 100 else ''}'")
            
        if not text:
            return jsonify({"error": "No text provided"}), 400
        
        if DEMO_MODE:
            print("Demo mode: generating synthetic PCM audio")
            pcm_data = generate_demo_pcm(text, sample_rate=sample_rate)
            print(f"Demo PCM generated: {len(pcm_data)} bytes")
            
            return Response(
                pcm_data,
                mimetype='audio/pcm',
                headers={
                    'Content-Type': 'audio/pcm',
                    'Content-Length': str(len(pcm_data))
                }
            )
        
        # Production mode: Use Google Cloud TTS REST API
        print(f"Requesting TTS from Google Cloud REST API with voice: {VOICE_NAME}")
        print(f"Sample rate: {sample_rate}")
        
        try:
            wav_data = call_google_tts_rest(text, sample_rate)
            
            if wav_data:
                # Extract PCM data from the WAV response
                pcm_data = extract_pcm_from_wav(wav_data)
                
                if pcm_data:
                    print(f"Extracted PCM audio: {len(pcm_data)} bytes")
                    
                    return Response(
                        pcm_data,
                        mimetype='audio/pcm',
                        headers={
                            'Content-Type': 'audio/pcm',
                            'Content-Length': str(len(pcm_data))
                        }
                    )
                else:
                    # Fallback: return the original WAV data
                    print("PCM extraction failed, returning WAV data")
                    return Response(
                        wav_data,
                        mimetype='audio/wav',
                        headers={
                            'Content-Type': 'audio/wav',
                            'Content-Length': str(len(wav_data))
                        }
                    )
            else:
                # Fallback to demo mode
                print("Google TTS failed, falling back to demo mode")
                pcm_data = generate_demo_pcm(text, sample_rate=sample_rate)
                print(f"Fallback demo PCM generated: {len(pcm_data)} bytes")
                
                return Response(
                    pcm_data,
                    mimetype='audio/pcm',
                    headers={
                        'Content-Type': 'audio/pcm',
                        'Content-Length': str(len(pcm_data))
                    }
                )
                
        except Exception as gcp_error:
            print(f"Google Cloud TTS error: {str(gcp_error)}")
            # Fallback to demo mode
            pcm_data = generate_demo_pcm(text, sample_rate=sample_rate)
            return Response(
                pcm_data,
                mimetype='audio/pcm',
                headers={
                    'Content-Type': 'audio/pcm',
                    'Content-Length': str(len(pcm_data))
                }
            )
            
    except Exception as e:
        print(f"TTS Error: {str(e)}")
        return jsonify({"error": f"TTS failed: {str(e)}"}), 500

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    status = {
        "status": "healthy",
        "demo_mode": DEMO_MODE,
        "tts_provider": "Google Cloud Text-to-Speech (REST API)",
        "voice_name": VOICE_NAME,
        "voice_language": VOICE_LANGUAGE,
        "credentials_configured": bool(GOOGLE_CLOUD_CREDENTIALS_PATH and os.path.exists(GOOGLE_CLOUD_CREDENTIALS_PATH))
    }
    return jsonify(status)

@app.route('/', methods=['GET'])
def root():
    """Root endpoint with basic info"""
    return jsonify({
        "service": "Google Cloud TTS Proxy for VAPI (Lambda)",
        "version": "4.0",
        "tts_provider": "Google Cloud Text-to-Speech (REST API)",
        "demo_mode": DEMO_MODE,
        "endpoints": {
            "tts": "/tts (POST)",
            "health": "/health (GET)"
        }
    })

# Lambda handler for AWS
def lambda_handler(event, context):
    """AWS Lambda handler that adapts API Gateway events to Flask"""
    try:
        print(f"Lambda handler called")
        print(f"Event keys: {list(event.keys())}")
        
        # Create a test client for Flask
        with app.test_client() as client:
            # Extract HTTP method and path
            method = event.get('httpMethod', event.get('requestContext', {}).get('http', {}).get('method', 'GET'))
            path = event.get('path', event.get('rawPath', '/'))
            
            print(f"Processing {method} {path}")
            
            # Handle query parameters
            query_params = event.get('queryStringParameters') or {}
            query_string = '&'.join([f"{k}={v}" for k, v in query_params.items()])
            if query_string:
                path += f"?{query_string}"
            
            # Extract headers
            headers = event.get('headers', {})
            
            # Extract body
            body = event.get('body', '')
            if event.get('isBase64Encoded', False):
                try:
                    body = base64.b64decode(body)
                except Exception as e:
                    print(f"Error decoding base64 body: {e}")
                    body = ''
            
            print(f"Request body length: {len(body) if body else 0}")
            
            # Make request to Flask app
            flask_response = client.open(
                method=method,
                path=path,
                headers=headers,
                data=body
            )
            
            print(f"Flask response status: {flask_response.status_code}")
            print(f"Flask response content type: {flask_response.headers.get('Content-Type')}")
            
            # Handle binary response
            response_data = flask_response.data
            is_binary = flask_response.headers.get('Content-Type', '').startswith('audio/')
            
            if is_binary:
                # Encode binary data as base64 for Lambda
                response_body = base64.b64encode(response_data).decode('utf-8')
                is_base64_encoded = True
                print(f"Binary response encoded: {len(response_body)} base64 chars")
            else:
                response_body = response_data.decode('utf-8')
                is_base64_encoded = False
                print(f"Text response: {len(response_body)} chars")
            
            lambda_response = {
                'statusCode': flask_response.status_code,
                'headers': dict(flask_response.headers),
                'body': response_body,
                'isBase64Encoded': is_base64_encoded
            }
            
            print(f"Lambda response prepared: {lambda_response['statusCode']}")
            return lambda_response
            
    except Exception as e:
        print(f"Lambda handler error: {str(e)}")
        print(f"Error type: {type(e).__name__}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        
        return {
            'statusCode': 500,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({
                'error': f'Lambda handler failed: {str(e)}',
                'error_type': type(e).__name__
            }),
            'isBase64Encoded': False
        }

if __name__ == '__main__':
    print("Starting Google Cloud TTS Proxy for VAPI (Lambda version)...")
    print(f"Demo mode: {DEMO_MODE}")
    if not DEMO_MODE:
        print(f"Voice: {VOICE_NAME} ({VOICE_LANGUAGE})")
    app.run(host='0.0.0.0', port=5000, debug=True)
