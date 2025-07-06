from flask import Flask, request, jsonify, Response
import requests
import os
import time
import uuid
from dotenv import load_dotenv
import io
import wave
import struct

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)

DEEPDUB_API_KEY = os.getenv("DEEPDUB_API_KEY")
VOICE_PROMPT_ID = os.getenv("DEEPDUB_VOICE_PROMPT_ID")
VAPI_SECRET = os.getenv("VAPI_SECRET", "deepdub-secret-2025")  # Default value for testing

# Demo mode for testing without real API credentials
DEMO_MODE = os.getenv("DEMO_MODE", "false").lower() == "true"

# Check required environment variables
if not DEEPDUB_API_KEY and not DEMO_MODE:
    print("WARNING: DEEPDUB_API_KEY environment variable not set!")
    print("Please set it before running the proxy, or set DEMO_MODE=true for testing.")
    
if not VOICE_PROMPT_ID and not DEMO_MODE:
    print("WARNING: DEEPDUB_VOICE_PROMPT_ID environment variable not set!")
    print("Please set it before running the proxy, or set DEMO_MODE=true for testing.")

if DEMO_MODE:
    print("🎭 DEMO MODE: Running without real Deepdub API calls")
else:
    print("🚀 PRODUCTION MODE: Using real Deepdub API")
    print(f"API Key: {DEEPDUB_API_KEY[:10]}..." if DEEPDUB_API_KEY else "API Key: None")
    print(f"Voice Prompt ID: {VOICE_PROMPT_ID}")

VALID_SAMPLE_RATES = [8000, 16000, 22050, 24000, 44100]

def convert_audio_to_pcm(audio_data, sample_rate=16000):
    """
    Convert audio data to raw PCM format that Vapi expects.
    
    For now, we'll assume the audio from Deepdub is already in a compatible format
    and try to extract PCM data from it. If it's MP3, we'll return the original data
    and let Vapi handle it, or we'll try to detect if it's WAV and extract PCM.
    
    Args:
        audio_data: Raw audio bytes (MP3, WAV, etc.)
        sample_rate: Target sample rate for PCM output
    
    Returns:
        Raw PCM bytes or original audio data
    """
    try:
        # Check if it's a WAV file by looking at the header
        if audio_data.startswith(b'RIFF') and b'WAVE' in audio_data[:12]:
            print("Detected WAV format, attempting to extract PCM data")
            
            # Try to parse WAV file and extract PCM data
            audio_buffer = io.BytesIO(audio_data)
            try:
                with wave.open(audio_buffer, 'rb') as wav_file:
                    # Get WAV parameters
                    channels = wav_file.getnchannels()
                    sample_width = wav_file.getsampwidth()
                    framerate = wav_file.getframerate()
                    
                    print(f"WAV info: {channels} channels, {sample_width} bytes/sample, {framerate} Hz")
                    
                    # Read all frames
                    frames = wav_file.readframes(wav_file.getnframes())
                    
                    # Convert to mono if stereo (simple approach - take left channel)
                    if channels == 2 and sample_width == 2:  # 16-bit stereo
                        # Convert stereo to mono by taking every other sample
                        mono_frames = bytearray()
                        for i in range(0, len(frames), 4):  # 4 bytes = 2 samples of 16-bit
                            if i + 1 < len(frames):
                                mono_frames.extend(frames[i:i+2])  # Take left channel
                        frames = bytes(mono_frames)
                        print(f"Converted stereo to mono, new size: {len(frames)} bytes")
                    
                    return frames
                    
            except Exception as wav_error:
                print(f"Failed to parse WAV file: {wav_error}")
                return audio_data
        else:
            print("Not a WAV file, returning original data")
            # For MP3 or other formats, return as-is for now
            # Vapi might be able to handle MP3 directly, or we'll need external tools
            return audio_data
            
    except Exception as e:
        print(f"Error in convert_audio_to_pcm: {e}")
        # Return original data as fallback
        return audio_data

@app.route("/tts", methods=["POST"])
def tts():
    request_id = str(uuid.uuid4())
    start_time = time.time()

    if request.headers.get("X-VAPI-SECRET") != VAPI_SECRET:
        return jsonify({"error": "Unauthorized"}), 401

    body = request.get_json()
    message = body.get("message")
    if not message:
        return jsonify({"error": "Missing message object"}), 400

    if message.get("type") != "voice-request":
        return jsonify({"error": "Invalid message type"}), 400

    text = message.get("text", "").strip()
    if not text:
        return jsonify({"error": "Invalid or missing text"}), 400

    sample_rate = message.get("sampleRate")
    if sample_rate not in VALID_SAMPLE_RATES:
        return jsonify({
            "error": "Unsupported sample rate",
            "supportedRates": VALID_SAMPLE_RATES
        }), 400

    print(f"TTS request started: {request_id} | Text length: {len(text)} | Sample rate: {sample_rate}Hz")
    print(f"Request text: '{text}'")
    print(f"DEMO_MODE: {DEMO_MODE}")
    print(f"API Key present: {bool(DEEPDUB_API_KEY)}")
    print(f"Voice Prompt ID present: {bool(VOICE_PROMPT_ID)}")

    # Check if required environment variables are set (unless in demo mode)
    if not DEMO_MODE:
        if not DEEPDUB_API_KEY:
            print(f"TTS failed: {request_id} | Missing DEEPDUB_API_KEY")
            return jsonify({"error": "Server configuration error: Missing API key"}), 500
        
        if not VOICE_PROMPT_ID:
            print(f"TTS failed: {request_id} | Missing DEEPDUB_VOICE_PROMPT_ID")
            return jsonify({"error": "Server configuration error: Missing voice prompt ID"}), 500

    try:
        if DEMO_MODE:
            # Demo mode: return a simple mock audio response
            print(f"TTS completed (DEMO): {request_id} | Duration: {time.time() - start_time:.2f}s")
            
            # Create a simple mock PCM audio (silence)
            duration = 2.0  # 2 seconds
            frames = int(duration * sample_rate)
            
            # Create raw PCM data (16-bit mono silence)
            pcm_data = b'\x00\x00' * frames  # 2 bytes per frame (16-bit)
            
            return Response(
                pcm_data,
                content_type="application/octet-stream",
                headers={
                    "Content-Length": str(len(pcm_data))
                }
            )
        else:
            # Real mode: Call Deepdub TTS
            deepdub_payload = {
                "model": "dd-etts-1.1",
                "targetText": text,
                "locale": "he-IL",
                "voicePromptId": VOICE_PROMPT_ID
            }
            
            print(f"Sending request to Deepdub API: {deepdub_payload}")
            print(f"Using API Key: {DEEPDUB_API_KEY[:10]}...")
            print(f"API URL: https://restapi.deepdub.ai/tts")
            
            try:
                r = requests.post(
                    "https://restapi.deepdub.ai/tts",
                    headers={
                        "Content-Type": "application/json",
                        "x-api-key": DEEPDUB_API_KEY
                    },
                    json=deepdub_payload,
                    timeout=25
                )
            except requests.exceptions.RequestException as req_error:
                print(f"Request failed: {req_error}")
                return jsonify({"error": f"Network error: {str(req_error)}"}), 500

            if r.status_code != 200:
                print(f"Deepdub API error: {r.status_code}")
                print(f"Response headers: {dict(r.headers)}")
                print(f"Response content: {r.text}")
                return jsonify({
                    "error": f"Deepdub TTS failed with status {r.status_code}",
                    "details": r.text
                }), 500

            print(f"Deepdub API response status: {r.status_code}")
            print(f"Deepdub API response headers: {dict(r.headers)}")
            print(f"Response content length: {len(r.text)}")
            print(f"Deepdub API response content: {r.text[:500]}...")  # First 500 chars
            
            if not r.text.strip():
                print("ERROR: Empty response from Deepdub API")
                return jsonify({"error": "Empty response from Deepdub API"}), 500
            
            # Check if response is JSON
            content_type = r.headers.get('content-type', '').lower()
            print(f"Response content-type: {content_type}")
            
            if 'application/json' in content_type:
                # JSON response with audioUrl (old format)
                try:
                    audio_json = r.json()
                    print(f"Successfully parsed JSON response")
                    print(f"JSON keys: {list(audio_json.keys()) if isinstance(audio_json, dict) else 'Not a dict'}")
                    
                    audio_url = audio_json.get("audioUrl")
                    if not audio_url:
                        return jsonify({"error": "Missing audioUrl in Deepdub response"}), 500

                    # Download audio from Deepdub's audioUrl
                    audio_response = requests.get(audio_url, stream=True)
                    if audio_response.status_code != 200:
                        return jsonify({"error": "Failed to fetch audio from audioUrl"}), 500

                    # Get the audio data
                    audio_data = audio_response.content
                    print(f"Downloaded audio data: {len(audio_data)} bytes")
                    
                    # Convert to PCM
                    pcm_data = convert_audio_to_pcm(audio_data, sample_rate)
                    print(f"Converted to PCM: {len(pcm_data)} bytes")

                    print(f"TTS completed: {request_id} | Duration: {time.time() - start_time:.2f}s")

                    return Response(
                        pcm_data,
                        content_type="application/octet-stream",
                        headers={
                            "Content-Length": str(len(pcm_data))
                        }
                    )
                    
                except ValueError as json_error:
                    print(f"Failed to parse JSON from Deepdub response: {json_error}")
                    print(f"Raw response content: {r.text}")
                    return jsonify({"error": f"Invalid JSON response from Deepdub API: {str(json_error)}", "raw_response": r.text[:200]}), 500
                    
            elif 'audio/' in content_type:
                # Direct audio response (new format)
                print(f"Received direct audio response: {content_type}")
                print(f"Audio content length: {len(r.content)} bytes")
                
                # Convert to PCM
                pcm_data = convert_audio_to_pcm(r.content, sample_rate)
                print(f"Converted to PCM: {len(pcm_data)} bytes")
                
                print(f"TTS completed: {request_id} | Duration: {time.time() - start_time:.2f}s")
                
                # Return the PCM data
                return Response(
                    pcm_data,
                    content_type="application/octet-stream",
                    headers={
                        "Content-Length": str(len(pcm_data))
                    }
                )
            else:
                # Unknown response format
                print(f"ERROR: Unexpected content type: {content_type}")
                print(f"Raw response: {r.text[:500]}")
                return jsonify({"error": f"Deepdub API returned unexpected response type: {content_type}"}), 500

    except Exception as e:
        print(f"TTS failed: {request_id} | Error: {str(e)}")
        return jsonify({"error": f"TTS synthesis failed", "requestId": request_id}), 500

@app.route("/")
def root():
    status = "🎭 DEMO MODE" if DEMO_MODE else "🚀 PRODUCTION MODE"
    return f"Deepdub TTS Proxy with streaming is running. {status}"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)