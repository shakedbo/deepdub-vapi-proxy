from flask import Flask, request, jsonify
import requests
import tempfile
import os

app = Flask(__name__)

DEEPDUB_API_KEY = os.getenv("DEEPDUB_API_KEY")
VOICE_PROMPT_ID = os.getenv("DEEPDUB_VOICE_PROMPT_ID")

@app.route("/tts", methods=["POST"])
def tts():
    data = request.get_json()
    text = data.get("text")

    if not text:
        return jsonify({"error": "Missing text"}), 400

    # Call Deepdub API
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
        }
    )

    if r.status_code != 200:
        return jsonify({"error": "Failed to call Deepdub API", "details": r.text}), 500

    # Save the mp3 file locally
    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as temp_audio:
        temp_audio.write(r.content)
        temp_audio_path = temp_audio.name

    # Serve as audioUrl back to Vapi (must be exposed publicly in production)
    return jsonify({
        "audioUrl": f"https://your-public-url.com/audio/{os.path.basename(temp_audio_path)}"
    })

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)