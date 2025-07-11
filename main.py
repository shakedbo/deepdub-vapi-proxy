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
from elevenlabs.client import ElevenLabs

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)

# ElevenLabs configuration
ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")
ELEVENLABS_VOICE_ID = os.getenv("ELEVENLABS_VOICE_ID")
ELEVENLABS_MODEL_ID = os.getenv("ELEVENLABS_MODEL_ID", "eleven_multilingual_v2")  # Default model

# VAPI configuration
VAPI_SECRET = os.getenv("VAPI_SECRET", "elevenlabs-secret-2025")  # Default value for testing

# Demo mode for testing without real API credentials
DEMO_MODE = os.getenv("DEMO_MODE", "false").lower() == "true"

# Initialize ElevenLabs client following official documentation
elevenlabs_client = ElevenLabs(
    api_key=ELEVENLABS_API_KEY
) if ELEVENLABS_API_KEY else None

# Check required environment variables
if not ELEVENLABS_API_KEY and not DEMO_MODE:
    print("WARNING: ELEVENLABS_API_KEY environment variable not set!")
    print("Please set it before running the proxy, or set DEMO_MODE=true for testing.")
    
if not ELEVENLABS_VOICE_ID and not DEMO_MODE:
    print("WARNING: ELEVENLABS_VOICE_ID environment variable not set!")
    print("Please set it before running the proxy, or set DEMO_MODE=true for testing.")

if DEMO_MODE:
    print("🎭 DEMO MODE: Running without real ElevenLabs API calls")
else:
    print("🚀 PRODUCTION MODE: Using real ElevenLabs API")
    print(f"API Key: {ELEVENLABS_API_KEY[:10]}..." if ELEVENLABS_API_KEY else "API Key: None")
    print(f"Voice ID: {ELEVENLABS_VOICE_ID}")
    print(f"Model ID: {ELEVENLABS_MODEL_ID}")

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

def apply_nikud(text):
    """
    Apply Hebrew diacritization (nikud) to text using Dicta Nakdan API.
    
    Args:
        text: Hebrew text to diacritize
    
    Returns:
        Diacritized text or original text if API fails
    """
    try:
        print(f"Applying nikud to text: '{text[:50]}{'...' if len(text) > 50 else ''}'")
        
        # Dicta Nakdan API endpoint
        nakdan_url = "https://nakdan-1.loadbalancer.dicta.org.il/addnikud"
        
        # Prepare payload
        payload = {
            "data": text,
            "corpus": "wiki",
            "keep_emojis": True
        }
        
        print(f"Sending request to Dicta Nakdan API...")
        
        # Make request with timeout
        response = requests.post(
            nakdan_url,
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=10  # 10 second timeout
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"Nakdan API response status: {response.status_code}")
            print(f"Response keys: {list(result.keys()) if isinstance(result, dict) else 'Not a dict'}")
            
            # Extract diacritized text - try "nikud_text" first, fallback to "data"
            nikud_text = result.get("nikud_text") or result.get("data")
            
            if nikud_text and nikud_text != text:
                print(f"✅ Successfully applied nikud")
                print(f"Original: '{text[:50]}{'...' if len(text) > 50 else ''}'")
                print(f"With nikud: '{nikud_text[:50]}{'...' if len(nikud_text) > 50 else ''}'")
                return nikud_text
            else:
                print("⚠️ Nakdan API returned same text or empty result, using original")
                return text
        else:
            print(f"❌ Nakdan API error: {response.status_code}")
            print(f"Response: {response.text[:200]}...")
            return text
            
    except requests.exceptions.Timeout:
        print("⚠️ Nakdan API timeout, using original text")
        return text
    except requests.exceptions.RequestException as e:
        print(f"⚠️ Nakdan API request failed: {e}, using original text")
        return text
    except Exception as e:
        print(f"⚠️ Error in apply_nikud: {e}, using original text")
        return text

def convert_audio_to_pcm(audio_data, sample_rate=16000):
    """
    Convert audio data to raw PCM format that Vapi expects.
    
    Supports WAV files natively. For MP3, uses pydub if available.
    
    Args:
        audio_data: Raw audio bytes (MP3, WAV, etc.)
        sample_rate: Target sample rate for PCM output
    
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
                        print("Note: Basic resampling - for best quality, ensure ElevenLabs returns correct sample rate")
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

    print(f"TTS request started: {request_id} | Text length: {len(text)} | Sample rate: {sample_rate}Hz")
    print(f"Request text: '{text}'")
    print(f"DEMO_MODE: {DEMO_MODE}")
    print(f"API Key present: {bool(ELEVENLABS_API_KEY)}")
    print(f"Voice ID present: {bool(ELEVENLABS_VOICE_ID)}")

    # Apply Hebrew diacritization (nikud) to the text
    text_with_nikud = apply_nikud(text)

    # Check if required environment variables are set (unless in demo mode)
    if not DEMO_MODE:
        if not ELEVENLABS_API_KEY:
            print(f"TTS failed: {request_id} | Missing ELEVENLABS_API_KEY")
            return jsonify({"error": "Server configuration error: Missing API key"}), 500
        
        if not ELEVENLABS_VOICE_ID:
            print(f"TTS failed: {request_id} | Missing ELEVENLABS_VOICE_ID")
            return jsonify({"error": "Server configuration error: Missing voice ID"}), 500

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
            # Real mode: Call ElevenLabs TTS
            print(f"Calling ElevenLabs TTS API for text: '{text_with_nikud[:50]}{'...' if len(text_with_nikud) > 50 else ''}'")
            print(f"Using Voice ID: {ELEVENLABS_VOICE_ID}")
            print(f"Using Model ID: {ELEVENLABS_MODEL_ID}")
            
            try:
                # Generate audio using ElevenLabs following official documentation
                print(f"Calling ElevenLabs TTS API for Hebrew text")
                print(f"Using Voice ID: {ELEVENLABS_VOICE_ID}")
                print(f"Using Model ID: {ELEVENLABS_MODEL_ID}")
                
                # Follow official ElevenLabs example pattern
                audio = elevenlabs_client.text_to_speech.convert(
                    text=text_with_nikud,  # Use the text with nikud
                    voice_id=ELEVENLABS_VOICE_ID,
                    model_id=ELEVENLABS_MODEL_ID,
                    output_format=f"pcm_{sample_rate}"  # Direct PCM for VAPI
                )
                
                # Convert audio generator to bytes (following official example)
                pcm_data = b"".join(audio)
                print(f"✅ Received PCM data directly from ElevenLabs: {len(pcm_data)} bytes")
                print("✅ No audio conversion needed - direct PCM to VAPI!")
                
                print(f"TTS completed: {request_id} | Duration: {time.time() - start_time:.2f}s")
                
                # Return the PCM data directly
                return Response(
                    pcm_data,
                    content_type="application/octet-stream",
                    headers={
                        "Content-Length": str(len(pcm_data))
                    }
                )
                
            except Exception as api_error:
                error_msg = str(api_error)
                print(f"ElevenLabs API error with {ELEVENLABS_MODEL_ID}: {error_msg}")
                
                # If v3 access denied, suggest contacting sales
                if "model_access_denied" in error_msg and "v3" in ELEVENLABS_MODEL_ID:
                    print("⚠️  Eleven v3 access denied - contact sales@elevenlabs.io for Hebrew support")
                    print("💡 Fallback: Try eleven_multilingual_v2 temporarily (limited Hebrew support)")
                    
                    # Try fallback to multilingual v2
                    try:
                        print("🔄 Attempting fallback to eleven_multilingual_v2...")
                        fallback_audio = elevenlabs_client.text_to_speech.convert(
                            text=text_with_nikud,
                            voice_id=ELEVENLABS_VOICE_ID,
                            model_id="eleven_multilingual_v2",
                            output_format=f"pcm_{sample_rate}"
                        )
                        
                        pcm_data = b"".join(fallback_audio)
                        print(f"✅ Fallback successful: {len(pcm_data)} bytes (limited Hebrew quality)")
                        
                        return Response(
                            pcm_data,
                            content_type="application/octet-stream",
                            headers={
                                "Content-Length": str(len(pcm_data))
                            }
                        )
                    except Exception as fallback_error:
                        print(f"❌ Fallback also failed: {fallback_error}")
                
                return jsonify({
                    "error": f"ElevenLabs TTS failed: {error_msg}",
                    "suggestion": "Contact sales@elevenlabs.io for Eleven v3 access for Hebrew support"
                }), 500

    except Exception as e:
        print(f"TTS failed: {request_id} | Error: {str(e)}")
        return jsonify({"error": f"TTS synthesis failed", "requestId": request_id}), 500

@app.route("/")
def root():
    status = "🎭 DEMO MODE" if DEMO_MODE else "🚀 PRODUCTION MODE"
    return f"ElevenLabs TTS Proxy with streaming is running. {status}"

if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port)