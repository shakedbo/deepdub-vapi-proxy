# Deepdub TTS Proxy for VAPI

This version is compatible with VAPI's custom-voice integration format. It converts audio from Deepdub API to raw PCM format that VAPI expects.

## Features

- ✅ Converts WAV audio to raw PCM (16-bit, mono) natively
- ✅ Full MP3 support via pydub + ffmpeg
- ✅ Demo mode for testing without real API credentials
- ✅ Supports both Deepdub response formats (JSON with audioUrl and direct audio)
- ✅ Proper error handling and logging
- ✅ Graceful fallback when pydub/ffmpeg not available

## Requirements

- Python 3.7+
- pydub for full audio processing
- ffmpeg for MP3 conversion

### Installing Dependencies

**pydub:**
```bash
pip install pydub
```

**ffmpeg:**

**Windows:**
```bash
# Using chocolatey
choco install ffmpeg

# Using winget
winget install ffmpeg

# Or download from https://ffmpeg.org/download.html
```

**macOS:**
```bash
brew install ffmpeg
```

**Linux:**
```bash
# Ubuntu/Debian
sudo apt update && sudo apt install ffmpeg

# CentOS/RHEL/Amazon Linux
sudo yum install ffmpeg
```

**For cloud deployment (Render.com, Heroku, etc.):**
Most cloud platforms support ffmpeg through buildpacks or packages. Check your platform's documentation.

## Environment Variables

- `DEEPDUB_API_KEY` - Your Deepdub API key
- `DEEPDUB_VOICE_PROMPT_ID` - Voice prompt ID from Deepdub
- `VAPI_SECRET` - Secret for VAPI authentication (default: deepdub-secret-2025)
- `DEMO_MODE` - Set to "true" for testing without real API calls

## Installation

```bash
pip install -r requirements.txt
```

## Usage

```bash
python main.py
```

## Deployment

### Option 1: Render.com with Docker (Recommended)

This proxy includes a Dockerfile with ffmpeg pre-installed for seamless cloud deployment.

1. **Connect to Render:**
   - Connect your GitHub repo to Render.com
   - Choose "Web Service" -> "Deploy an existing image from a registry" or "Build from source"

2. **Configure Environment Variables in Render Dashboard:**
   ```
   DEEPDUB_API_KEY=your_api_key_here
   DEEPDUB_VOICE_PROMPT_ID=your_voice_prompt_id_here
   VAPI_SECRET=your_custom_secret
   ```

3. **Deploy:**
   - Render will automatically build the Docker image with ffmpeg
   - No additional configuration needed!

### Option 2: Manual Installation

For local development or other platforms:

**WAV files**: Always processed natively (no external dependencies)  
**MP3 files**: Converted with pydub/ffmpeg if available, otherwise returned as-is  
**Other formats**: Returned as-is for VAPI to handle

### Docker Commands

**Build locally:**
```bash
docker build -t deepdub-vapi-proxy .
```

**Run locally:**
```bash
docker run -p 5000:5000 \
  -e DEEPDUB_API_KEY=your_key \
  -e DEEPDUB_VOICE_PROMPT_ID=your_prompt_id \
  deepdub-vapi-proxy
```

**Run with demo mode:**
```bash
docker run -p 5000:5000 -e DEMO_MODE=true deepdub-vapi-proxy
```

**Using Docker Compose (recommended for development):**
```bash
# Copy environment file
cp .env.example .env
# Edit .env with your credentials
# Run in demo mode
docker-compose up
```

## Audio Format

The proxy converts audio to VAPI's expected format:
- **Format**: Raw PCM
- **Sample rate**: As requested by VAPI (8000, 16000, 22050, 24000, or 44100 Hz)
- **Channels**: Mono
- **Bit depth**: 16-bit
- **Content-Type**: application/octet-stream

## Troubleshooting

If you see warnings about pydub not being available:
1. Install pydub: `pip install pydub`
2. Install ffmpeg (see instructions above)
3. Restart the proxy

The proxy will still work with WAV files even without pydub/ffmpeg.

## API Usage

Use this with VAPI's `custom-voice` provider. Expects POST requests with VAPI's voice-request format.

**Example request:**
```bash
curl -X POST http://your-render-url.com/tts \
  -H "Content-Type: application/json" \
  -H "X-VAPI-SECRET: your-secret" \
  -d '{
    "message": {
      "type": "voice-request",
      "text": "Hello world!",
      "sampleRate": 16000
    }
  }'
```

**Response:**
- Content-Type: `application/octet-stream`
- Body: Raw PCM audio data (16-bit, mono)

## Render.com Quick Deploy

[![Deploy to Render](https://render.com/images/deploy-to-render-button.svg)](https://render.com/deploy)

1. Click the button above
2. Set your environment variables:
   - `DEEPDUB_API_KEY`
   - `DEEPDUB_VOICE_PROMPT_ID`
   - `VAPI_SECRET` (optional)
3. Deploy!

The Docker container includes ffmpeg and all dependencies pre-installed.