from flask import Flask, request, jsonify, Response
import requests
import os
import time
import uuid
from dotenv import load_dotenv
import io
import wave
import struct
import tempfile

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

# Check if pydub is available for audio conversion
def check_pydub_available():
    """Check if pydub is available and can handle audio conversion"""
    try:
        from pydub import AudioSegment
        # Test if we can create a simple audio segment (this will fail if dependencies are missing)
        test_audio = AudioSegment.silent(duration=100)
        return True
    except ImportError:
        return False
    except Exception:
        # pydub might be installed but missing dependencies (ffmpeg, etc.)
        return False

# Check pydub availability at startup
PYDUB_AVAILABLE = check_pydub_available()
if not PYDUB_AVAILABLE:
    print("⚠️  pydub not available or missing dependencies!")
    print("   For full MP3 support, install: pip install pydub")
    print("   And ensure ffmpeg is available on the system")
    print("   WAV files will still be processed natively")
else:
    print("✅ pydub found - full audio conversion available")

VALID_SAMPLE_RATES = [8000, 16000, 22050, 24000, 44100]
SAMPLE_RATE = 8000  # Default sample rate for PCM conversion

def convert_audio_to_pcm(audio_data, sample_rate=SAMPLE_RATE):
    """
    Convert audio data to raw PCM format that Vapi expects.
    
    Supports WAV files natively. For MP3, uses pydub if available.
    
    Args:
        audio_data: Raw audio bytes (MP3, WAV, etc.)
        sample_rate: Target sample rate for PCM output (default 8000Hz)
    
    Returns:
        Raw PCM bytes (16-bit, mono) or original data if conversion fails
    """
    try:
        # Check if it's a WAV file by looking at the header first (faster)
        if audio_data.startswith(b'RIFF') and b'WAVE' in audio_data[:12]:
            print("Detected WAV format, attempting to extract PCM data")
            
            # Try to parse WAV file and extract PCM data using wave module (faster)
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
                    
                    # Simple resample if needed (basic approach)
                    if framerate != sample_rate:
                        print(f"WAV sample rate ({framerate}Hz) doesn't match target ({sample_rate}Hz)")
                        print("Note: Basic resampling - for best quality, ensure Deepdub returns correct sample rate")
                        # For now, we'll keep the original rate and let VAPI handle it
                        # Advanced resampling would require additional libraries
                    
                    # Convert to mono if stereo (simple approach - take left channel)
                    if channels == 2 and sample_width == 2:  # 16-bit stereo
                        # Convert stereo to mono by taking every other sample
                        mono_frames = bytearray()
                        for i in range(0, len(frames), 4):  # 4 bytes = 2 samples of 16-bit
                            if i + 1 < len(frames):
                                mono_frames.extend(frames[i:i+2])  # Take left channel
                        frames = bytes(mono_frames)
                        print(f"Converted stereo to mono, new size: {len(frames)} bytes")
                    
                    # Ensure 16-bit format
                    if sample_width != 2:
                        print(f"Warning: WAV is {sample_width * 8}-bit, expected 16-bit")
                        print("Advanced bit depth conversion requires additional libraries")
                        # For now, return as-is and let VAPI handle it
                    
                    return frames
                    
            except Exception as wav_error:
                print(f"Failed to parse WAV file with wave module: {wav_error}")
                print("Falling back to pydub for WAV processing")
                # Fall through to pydub processing below
        
        # For all other formats (MP3, or WAV that failed above), use pydub
        if not PYDUB_AVAILABLE:
            print("pydub not available - cannot convert audio to PCM")
            print("Returning original audio data (Vapi may not support this)")
            return audio_data
        
        try:
            from pydub import AudioSegment
            
            print(f"Using pydub to convert audio to PCM (target: {sample_rate}Hz, 16-bit, mono)")
            
            # Load audio from bytes using pydub
            audio_buffer = io.BytesIO(audio_data)
            
            # Try to detect format and load
            if audio_data.startswith(b'ID3') or audio_data.startswith(b'\xff\xfb') or audio_data.startswith(b'\xff\xfa'):
                print("Loading as MP3")
                audio = AudioSegment.from_mp3(audio_buffer)
            elif audio_data.startswith(b'RIFF') and b'WAVE' in audio_data[:12]:
                print("Loading as WAV")
                audio = AudioSegment.from_wav(audio_buffer)
            else:
                print("Unknown format, trying auto-detection")
                audio = AudioSegment.from_file(audio_buffer)
            
            print(f"Original audio: {audio.channels} channels, {audio.frame_rate}Hz, {audio.sample_width * 8}-bit")
            
            # Convert to target sample rate
            if audio.frame_rate != sample_rate:
                print(f"Resampling from {audio.frame_rate}Hz to {sample_rate}Hz")
                audio = audio.set_frame_rate(sample_rate)
            
            # Convert to mono if stereo
            if audio.channels > 1:
                print("Converting to mono")
                audio = audio.set_channels(1)
            
            # Convert to 16-bit
            if audio.sample_width != 2:
                print(f"Converting from {audio.sample_width * 8}-bit to 16-bit")
                audio = audio.set_sample_width(2)
            
            # Export as raw PCM data
            pcm_buffer = io.BytesIO()
            audio.export(pcm_buffer, format="raw")
            pcm_data = pcm_buffer.getvalue()
            
            print(f"Successfully converted to PCM: {len(pcm_data)} bytes")
            return pcm_data
            
        except Exception as pydub_error:
            print(f"Failed to convert audio with pydub: {pydub_error}")
            print("Returning original audio data as fallback")
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

    # Set default speed to 1.3 for slightly faster, more natural speech
    # Since VAPI doesn't send speed parameter, we use a faster default
    speed = 1.3  # 30% faster than normal speed

    print(f"TTS request started: {request_id} | Text length: {len(text)} | Sample rate: {sample_rate}Hz | Speed: {speed}x")
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
                "model": "dd-etts-2.5",
                "targetText": text,
                "format": "wav",
                "sampleRate": 8000,
                "locale": "he-IL",
                "voicePromptId": VOICE_PROMPT_ID,
                "speed": speed  # Add speed control for faster speech
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
                    
            elif 'audio/' in content_type or 'text/plain' in content_type:
                # Direct audio response (new format) or binary data with text/plain content-type
                print(f"Received direct audio response: {content_type}")
                print(f"Audio content length: {len(r.content)} bytes")
                
                # Convert to PCM at 8000Hz
                pcm_data = convert_audio_to_pcm(r.content, 8000)  # Force 8000Hz as requested
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
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port)