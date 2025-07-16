"""
Google Cloud TTS Proxy for VAPI

Features:
- Supports Hebrew text-to-speech (he-IL-Wavenet-D)
- Returns native PCM audio format (LINEAR16)
- Compatible with VAPI requirements
- AWS Lambda deployment ready
"""

import os
import io
import wave
import json
import base64
import math
from flask import Flask, request, Response, jsonify
from dotenv import load_dotenv
from google.cloud import texttospeech

load_dotenv()
app = Flask(__name__)

# Environment variables
GOOGLE_CLOUD_CREDENTIALS_PATH = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
VOICE_NAME = os.getenv("VOICE_NAME", "he-IL-Wavenet-D")
VOICE_LANGUAGE = os.getenv("VOICE_LANGUAGE", "he-IL")
DEMO_MODE = os.getenv("DEMO_MODE", "false").lower() == "true"

# Initialize Google Cloud TTS client
tts_client = None
if not DEMO_MODE:
    try:
        if GOOGLE_CLOUD_CREDENTIALS_PATH:
            # Try different credential file locations for Lambda compatibility
            for path in [GOOGLE_CLOUD_CREDENTIALS_PATH, f"/tmp/{GOOGLE_CLOUD_CREDENTIALS_PATH}", f"./{GOOGLE_CLOUD_CREDENTIALS_PATH}"]:
                if os.path.exists(path):
                    print(f"Found credentials file at: {path}")
                    tts_client = texttospeech.TextToSpeechClient.from_service_account_file(path)
                    break
            
            if not tts_client:
                print("Credentials file not found, trying default credentials...")
                tts_client = texttospeech.TextToSpeechClient()
        else:
            tts_client = texttospeech.TextToSpeechClient()
            
        if tts_client:
            print(f"Google Cloud TTS client initialized successfully")
            print(f"Voice: {VOICE_NAME}, Language: {VOICE_LANGUAGE}")
        else:
            print("Failed to initialize TTS client, switching to demo mode")
            DEMO_MODE = True
            
    except Exception as e:
        print(f"Error initializing Google Cloud TTS client: {str(e)}")
        print("Switching to demo mode")
        tts_client = None
        DEMO_MODE = True
else:
    print("DEMO MODE: Running without real Google Cloud TTS API calls")

def generate_demo_pcm(text, sample_rate=24000, duration_seconds=2):
    """Generate demo PCM audio for testing"""
    num_samples = int(sample_rate * duration_seconds)
    pcm_data = bytearray()
    
    for i in range(num_samples):
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
        
        # Handle VAPI format or simple format
        if 'message' in data:
            message = data['message']
            text = message.get('text', '')
            sample_rate = message.get('sampleRate', 24000)
            print(f"VAPI format - text: '{text[:100]}{'...' if len(text) > 100 else ''}'")
        else:
            text = data.get('text', '')
            sample_rate = 24000
            print(f"Simple format - text: '{text[:100]}{'...' if len(text) > 100 else ''}'")
            
        if not text:
            return jsonify({"error": "No text provided"}), 400
        
        if DEMO_MODE or tts_client is None:
            print("Demo mode: generating synthetic PCM audio")
            pcm_data = generate_demo_pcm(text, sample_rate=sample_rate)
            print(f"Demo PCM generated: {len(pcm_data)} bytes")
            
            return Response(
                pcm_data,
                mimetype='audio/pcm',
                headers={'Content-Type': 'audio/pcm', 'Content-Length': str(len(pcm_data))}
            )
        
        # Production mode: Use Google Cloud TTS
        print(f"Requesting TTS from Google Cloud with voice: {VOICE_NAME}")
        
        try:
            synthesis_input = texttospeech.SynthesisInput(text=text)
            voice = texttospeech.VoiceSelectionParams(language_code=VOICE_LANGUAGE, name=VOICE_NAME)
            audio_config = texttospeech.AudioConfig(
                audio_encoding=texttospeech.AudioEncoding.LINEAR16,
                sample_rate_hertz=sample_rate
            )
            
            response = tts_client.synthesize_speech(
                input=synthesis_input, voice=voice, audio_config=audio_config
            )
            
            pcm_data = extract_pcm_from_wav(response.audio_content)
            
            if pcm_data:
                print(f"Received PCM audio: {len(pcm_data)} bytes")
                return Response(
                    pcm_data,
                    mimetype='audio/pcm',
                    headers={'Content-Type': 'audio/pcm', 'Content-Length': str(len(pcm_data))}
                )
            else:
                print("PCM extraction failed, returning WAV data")
                return Response(
                    response.audio_content,
                    mimetype='audio/wav',
                    headers={'Content-Type': 'audio/wav', 'Content-Length': str(len(response.audio_content))}
                )
                
        except Exception as gcp_error:
            print(f"Google Cloud TTS error: {str(gcp_error)}")
            return jsonify({"error": f"TTS failed: {str(gcp_error)}"}), 500
            
    except Exception as e:
        print(f"TTS Error: {str(e)}")
        return jsonify({"error": f"TTS failed: {str(e)}"}), 500

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "demo_mode": DEMO_MODE,
        "tts_provider": "Google Cloud Text-to-Speech",
        "voice_name": VOICE_NAME,
        "voice_language": VOICE_LANGUAGE,
        "client_initialized": tts_client is not None
    })

@app.route('/', methods=['GET'])
def root():
    """Root endpoint with basic info"""
    return jsonify({
        "service": "Google Cloud TTS Proxy for VAPI",
        "version": "4.0",
        "tts_provider": "Google Cloud Text-to-Speech",
        "endpoints": {"tts": "/tts (POST)", "health": "/health (GET)"}
    })

def lambda_handler(event, context):
    """AWS Lambda handler that adapts API Gateway events to Flask"""
    try:
        print(f"Lambda handler called for {event.get('httpMethod', 'UNKNOWN')} {event.get('path', '/')}")
        
        with app.test_client() as client:
            method = event.get('httpMethod', event.get('requestContext', {}).get('http', {}).get('method', 'GET'))
            path = event.get('path', event.get('rawPath', '/'))
            
            # Strip stage prefix if present (e.g., /prod/tts -> /tts)
            if path.startswith('/prod/'):
                path = path[5:]
            
            headers = event.get('headers', {})
            body = event.get('body', '')
            
            if event.get('isBase64Encoded', False):
                try:
                    body = base64.b64decode(body)
                except Exception as e:
                    print(f"Error decoding base64 body: {e}")
                    body = ''
            
            flask_response = client.open(method=method, path=path, headers=headers, data=body)
            
            response_data = flask_response.data
            is_binary = flask_response.headers.get('Content-Type', '').startswith('audio/')
            
            if is_binary:
                response_body = base64.b64encode(response_data).decode('utf-8')
                is_base64_encoded = True
            else:
                response_body = response_data.decode('utf-8')
                is_base64_encoded = False
            
            return {
                'statusCode': flask_response.status_code,
                'headers': dict(flask_response.headers),
                'body': response_body,
                'isBase64Encoded': is_base64_encoded
            }
            
    except Exception as e:
        print(f"Lambda handler error: {str(e)}")
        return {
            'statusCode': 500,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({'error': f'Lambda handler failed: {str(e)}'}),
            'isBase64Encoded': False
        }

if __name__ == '__main__':
    print("Starting Google Cloud TTS Proxy for VAPI...")
    print(f"Demo mode: {DEMO_MODE}")
    if not DEMO_MODE:
        print(f"Voice: {VOICE_NAME} ({VOICE_LANGUAGE})")
    app.run(host='0.0.0.0', port=5000, debug=True)