# Deepdub TTS Proxy for VAPI

A simple Flask proxy that converts text to speech using the Deepdub API and returns PCM audio for VAPI integration.

## Features

- **PCM Audio Output**: Returns raw PCM audio data optimized for VAPI
- **Deepdub SDK Integration**: Uses the official Deepdub Python SDK
- **AWS Lambda Support**: Deployable to AWS Lambda with API Gateway
- **Demo Mode**: Built-in test mode for development
- **Health Checks**: Health endpoint for monitoring

## Quick Start

### Local Development

1. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Set up environment variables**:
   ```bash
   cp .env.example .env
   # Edit .env with your Deepdub credentials
   ```

3. **Run locally**:
   ```bash
   python main.py
   ```

4. **Test the service**:
   ```bash
   python test_deepdub.py
   ```

### Environment Variables

- `DEEPDUB_API_KEY`: Your Deepdub API key
- `DEEPDUB_VOICE_PROMPT_ID`: Voice prompt ID to use for TTS
- `DEMO_MODE`: Set to "true" for testing without real API calls
- `VAPI_SECRET`: Optional secret for VAPI integration

### API Endpoints

- `POST /tts`: Convert text to PCM audio
  ```json
  {"text": "Hello world"}
  ```

- `GET /health`: Health check endpoint
- `GET /`: Service info

### AWS Lambda Deployment

The service can be deployed to AWS Lambda using `lambda_function.py` as the handler.

## Development

### Project Structure

```
├── main.py              # Flask application
├── lambda_function.py   # AWS Lambda handler
├── requirements.txt     # Python dependencies
├── test_deepdub.py     # Test script
├── .env                # Environment variables
└── README.md           # This file
```

### Dependencies

- Flask 2.3.3
- requests 2.31.0
- python-dotenv 1.0.0
- deepdub 0.1.14

## License

MIT License