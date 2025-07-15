"""
Google Cloud TTS Proxy for VAPI

Features:
- Supports Hebrew text-to-speech
- Returns native PCM audio format (LINEAR16)
- Compatible with VAPI requirements
- Configurable sample rates and voices
"""

import os
import io
import wave
from flask import Flask, request, Response, jsonify
from dotenv import load_dotenv
from google.cloud import texttospeech

load_dotenv()

app = Flask(__name__)

# Environment variables
GOOGLE_CLOUD_CREDENTIALS_PATH = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
VOICE_NAME = os.getenv("VOICE_NAME", "he-IL-Wavenet-A")  # Hebrew voice
VOICE_LANGUAGE = os.getenv("VOICE_LANGUAGE", "he-IL")  # Hebrew locale
VAPI_SECRET = os.getenv("VAPI_SECRET", "deepdub-secret-2025")
DEMO_MODE = os.getenv("DEMO_MODE", "false").lower() == "true"

# Initialize Google Cloud TTS client
if not DEMO_MODE:
    try:
        if GOOGLE_CLOUD_CREDENTIALS_PATH and os.path.exists(GOOGLE_CLOUD_CREDENTIALS_PATH):
            # Use credentials file if provided
            tts_client = texttospeech.TextToSpeechClient.from_service_account_file(GOOGLE_CLOUD_CREDENTIALS_PATH)
            print(f"Google Cloud TTS client initialized with credentials file: {GOOGLE_CLOUD_CREDENTIALS_PATH}")
        else:
            # Use default credentials (from environment or gcloud auth)
            tts_client = texttospeech.TextToSpeechClient()
            print("Google Cloud TTS client initialized with default credentials")
        print(f"Voice: {VOICE_NAME}, Language: {VOICE_LANGUAGE}")
    except Exception as e:
        print(f"Failed to initialize Google Cloud TTS client: {e}")
        tts_client = None
        print("Running in DEMO MODE due to initialization failure")
        DEMO_MODE = True
else:
    tts_client = None
    print("DEMO MODE: Running without real Google Cloud TTS API calls")

def generate_demo_pcm(text, sample_rate=24000, duration_seconds=2):
    """Generate demo PCM audio for testing"""
    import math
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
        
        # Production mode: Use Google Cloud TTS
        print(f"Requesting TTS from Google Cloud with voice: {VOICE_NAME}")
        print(f"Sample rate: {sample_rate}")
        
        try:
            # Configure the synthesis input
            synthesis_input = texttospeech.SynthesisInput(text=text)
            
            # Configure the voice
            voice = texttospeech.VoiceSelectionParams(
                language_code=VOICE_LANGUAGE,
                name=VOICE_NAME
            )
            
            # Configure the audio format - LINEAR16 is PCM in WAV container
            audio_config = texttospeech.AudioConfig(
                audio_encoding=texttospeech.AudioEncoding.LINEAR16,
                sample_rate_hertz=sample_rate
            )
            
            # Perform the TTS request
            response = tts_client.synthesize_speech(
                input=synthesis_input,
                voice=voice,
                audio_config=audio_config
            )
            
            # Extract PCM data from the WAV response
            pcm_data = extract_pcm_from_wav(response.audio_content)
            
            if pcm_data:
                print(f"Received PCM audio from Google Cloud TTS: {len(pcm_data)} bytes")
                
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
                    response.audio_content,
                    mimetype='audio/wav',
                    headers={
                        'Content-Type': 'audio/wav',
                        'Content-Length': str(len(response.audio_content))
                    }
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
    status = {
        "status": "healthy",
        "demo_mode": DEMO_MODE,
        "tts_provider": "Google Cloud Text-to-Speech",
        "voice_name": VOICE_NAME,
        "voice_language": VOICE_LANGUAGE,
        "credentials_configured": bool(GOOGLE_CLOUD_CREDENTIALS_PATH),
        "client_initialized": tts_client is not None
    }
    return jsonify(status)

@app.route('/', methods=['GET'])
def root():
    """Root endpoint with basic info"""
    return jsonify({
        "service": "Google Cloud TTS Proxy for VAPI",
        "version": "3.0",
        "tts_provider": "Google Cloud Text-to-Speech",
        "demo_mode": DEMO_MODE,
        "endpoints": {
            "tts": "/tts (POST)",
            "health": "/health (GET)"
        }
    })

if __name__ == '__main__':
    print("Starting Google Cloud TTS Proxy for VAPI...")
    print(f"Demo mode: {DEMO_MODE}")
    if not DEMO_MODE:
        print(f"Voice: {VOICE_NAME} ({VOICE_LANGUAGE})")
    app.run(host='0.0.0.0', port=5000, debug=True)
