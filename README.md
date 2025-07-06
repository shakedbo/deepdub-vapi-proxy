# Deepdub TTS Proxy for VAPI

This version is compatible with VAPI's custom-voice integration format. It converts audio from Deepdub API to raw PCM format that VAPI expects.

## Features

- ✅ Converts WAV audio to raw PCM (16-bit, mono) natively
- ✅ MP3 support via pydub (optional - fallback to original format if not available)
- ✅ Demo mode for testing without real API credentials
- ✅ Supports both Deepdub response formats (JSON with audioUrl and direct audio)
- ✅ Proper error handling and logging
- ✅ **Perfect for cloud deployment** - works without external dependencies
- ✅ **Render.com ready** - no ffmpeg or system tools required

## Requirements

- Python 3.7+
- Only standard libraries required for basic WAV processing
- Optional: pydub for enhanced MP3 support (will work without it)

## Environment Variables

- `DEEPDUB_API_KEY` - Your Deepdub API key
- `DEEPDUB_VOICE_PROMPT_ID` - Voice prompt ID from Deepdub
- `VAPI_SECRET` - Secret for VAPI authentication (default: deepdub-secret-2025)
- `DEMO_MODE` - Set to "true" for testing without real API calls

## Installation

```bash
pip install -r requirements.txt
```

### Optional Enhanced MP3 Support

If you want full MP3 to PCM conversion (most TTS services return WAV anyway):

```bash
pip install pydub
```

Note: On Python 3.13, pydub may have compatibility issues. The proxy works perfectly without it for WAV files.

## Usage

```bash
python main.py
```

## Deployment

This proxy is specifically designed for cloud platforms like **Render.com**:

- ✅ No external dependencies (ffmpeg, etc.)
- ✅ Pure Python implementation
- ✅ Handles WAV files (most common TTS format) natively
- ✅ Graceful fallback for other formats

Use this with VAPI's `custom-voice` provider. Expects POST requests with VAPI's voice-request format.

## Audio Format

The proxy converts audio to VAPI's expected format:
- **Format**: Raw PCM
- **Sample rate**: As requested by VAPI (8000, 16000, 22050, 24000, or 44100 Hz)
- **Channels**: Mono
- **Bit depth**: 16-bit
- **Content-Type**: application/octet-stream

## Render.com Deployment

1. Connect your GitHub repo to Render.com
2. Set environment variables in Render dashboard
3. Deploy - no additional configuration needed!

The proxy automatically detects available libraries and adapts accordingly.