import os
import io
from flask import Flask, request, Response, jsonify
from dotenv import load_dotenv
from deepdub import DeepdubClient

load_dotenv()

app = Flask(__name__)

# Environment variables
DEEPDUB_API_KEY = os.getenv("DEEPDUB_API_KEY")
VOICE_PROMPT_ID = os.getenv("DEEPDUB_VOICE_PROMPT_ID")
VAPI_SECRET = os.getenv("VAPI_SECRET", "deepdub-secret-2025")
DEMO_MODE = os.getenv("DEMO_MODE", "false").lower() == "true"

# Initialize Deepdub client
if not DEMO_MODE:
    dd_client = DeepdubClient(api_key=DEEPDUB_API_KEY)
    print("PRODUCTION MODE: Using Deepdub SDK for TTS")
else:
    dd_client = None
    print("DEMO MODE: Running without real Deepdub API calls")

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
        
        # Production mode: Use Deepdub SDK with PCM format
        print(f"Requesting TTS from Deepdub SDK with voice: {VOICE_PROMPT_ID}")
        print(f"Sample rate: {sample_rate}")
        
        try:
            audio_data = dd_client.tts(
                text=text,
                voice_prompt_id=VOICE_PROMPT_ID,
                model="dd-etts-2.5",
                locale="he-IL",  # Hebrew locale as in your example
                prompt_boost=True,
                realtime=True,
                format="pcm",  # Request PCM format directly
                sample_rate=sample_rate
            )
            
            if isinstance(audio_data, bytes):
                print(f"Received PCM audio from Deepdub: {len(audio_data)} bytes")
                
                return Response(
                    audio_data,
                    mimetype='audio/pcm',
                    headers={
                        'Content-Type': 'audio/pcm',
                        'Content-Length': str(len(audio_data))
                    }
                )
            else:
                print(f"Unexpected audio data type: {type(audio_data)}")
                return jsonify({"error": "Invalid audio data received from Deepdub"}), 500
                
        except Exception as deepdub_error:
            print(f"Deepdub SDK error: {str(deepdub_error)}")
            
            # Fallback: try without PCM format (get MP3 and note it)
            try:
                print("Fallback: requesting MP3 from Deepdub (will need conversion)")
                audio_data = dd_client.tts(
                    text=text,
                    voice_prompt_id=VOICE_PROMPT_ID,
                    model="dd-etts-2.5",
                    locale="he-IL",
                    prompt_boost=True,
                    realtime=True
                    # No format specified - will get MP3
                )
                
                if isinstance(audio_data, bytes):
                    print(f"Received MP3 audio from Deepdub: {len(audio_data)} bytes")
                    print("WARNING: Returning MP3 instead of PCM - VAPI may not accept this")
                    
                    return Response(
                        audio_data,
                        mimetype='audio/mpeg',
                        headers={
                            'Content-Type': 'audio/mpeg',
                            'Content-Length': str(len(audio_data))
                        }
                    )
                else:
                    return jsonify({"error": "Invalid audio data received from Deepdub"}), 500
                    
            except Exception as fallback_error:
                print(f"Fallback also failed: {str(fallback_error)}")
                return jsonify({"error": f"TTS failed: {str(fallback_error)}"}), 500
            
    except Exception as e:
        print(f"TTS Error: {str(e)}")
        return jsonify({"error": f"TTS failed: {str(e)}"}), 500

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    status = {
        "status": "healthy",
        "demo_mode": DEMO_MODE,
        "deepdub_configured": bool(DEEPDUB_API_KEY),
        "voice_id_configured": bool(VOICE_PROMPT_ID)
    }
    return jsonify(status)

@app.route('/', methods=['GET'])
def root():
    """Root endpoint with basic info"""
    return jsonify({
        "service": "Deepdub TTS Proxy for VAPI",
        "version": "2.0",
        "demo_mode": DEMO_MODE,
        "endpoints": {
            "tts": "/tts (POST)",
            "health": "/health (GET)"
        }
    })

if __name__ == '__main__':
    print("Starting Deepdub TTS Proxy for VAPI...")
    print(f"Demo mode: {DEMO_MODE}")
    if not DEMO_MODE:
        print(f"Voice ID: {VOICE_PROMPT_ID}")
    app.run(host='0.0.0.0', port=5000, debug=True)