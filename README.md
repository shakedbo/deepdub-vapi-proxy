# Deepdub TTS Proxy for VAPI

This version is compatible with VAPI's custom-voice integration format.

## Environment Variables

- `DEEPDUB_API_KEY`
- `DEEPDUB_VOICE_PROMPT_ID`
- `VAPI_SECRET` (default: deepdub-secret-2025)

## Deployment

Use this with VAPI's `custom-voice` provider. Expects POST requests with VAPI's voice-request format.