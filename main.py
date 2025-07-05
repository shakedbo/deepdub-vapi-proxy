from flask import Flask, request, jsonify, Response
import requests
import os
import time
import uuid

app = Flask(__name__)

DEEPDUB_API_KEY = os.getenv("DEEPDUB_API_KEY")
VOICE_PROMPT_ID = os.getenv("DEEPDUB_VOICE_PROMPT_ID")
VAPI_SECRET = os.getenv("VAPI_SECRET")

VALID_SAMPLE_RATES = [8000, 16000, 22050, 24000, 44100]

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

    try:
        # Call Deepdub TTS
        r = requests.post(
            "https://restapi.deepdub.ai/tts",
            headers={
                "Content-Type": "application/json",
                "x-api-key": DEEPDUB_API_KEY
            },
            json={
                "model": "dd-etts-1.1",
                "targetText": text,
                "locale": "he-IL",
                "voicePromptId": VOICE_PROMPT_ID
            },
            timeout=25
        )

        if r.status_code != 200:
            print(f"Deepdub API error: {r.status_code}, {r.text}")
            return jsonify({"error": "Deepdub TTS failed"}), 500

        audio_json = r.json()
        audio_url = audio_json.get("audioUrl")

        if not audio_url:
            return jsonify({"error": "Missing audioUrl in Deepdub response"}), 500

        # Stream audio from Deepdub's audioUrl
        audio_response = requests.get(audio_url, stream=True)
        if audio_response.status_code != 200:
            return jsonify({"error": "Failed to fetch audio from audioUrl"}), 500

        print(f"TTS completed: {request_id} | Duration: {time.time() - start_time:.2f}s")

        return Response(
            audio_response.iter_content(chunk_size=4096),
            content_type="application/octet-stream"
        )

    except Exception as e:
        print(f"TTS failed: {request_id} | Error: {str(e)}")
        return jsonify({"error": "TTS synthesis failed", "requestId": request_id}), 500

@app.route("/")
def root():
    return "Deepdub TTS Proxy with streaming is running."

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)