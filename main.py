from flask import Flask, request, jsonify, send_from_directory
import requests
import tempfile
import os

app = Flask(__name__)

DEEPDUB_API_KEY = os.getenv("DEEPDUB_API_KEY")
VOICE_PROMPT_ID = os.getenv("DEEPDUB_VOICE_PROMPT_ID")

AUDIO_FOLDER = "/tmp/deepdub_audio"
os.makedirs(AUDIO_FOLDER, exist_ok=True)

@app.route("/tts", methods=["POST"])
def tts():
    data = request.get_json()
    text = data.get("text")

    if not text:
        return jsonify({"error": "Missing text"}), 400

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

    filename = next(tempfile._get_candidate_names()) + ".mp3"
    path = os.path.join(AUDIO_FOLDER, filename)

    with open(path, "wb") as f:
        f.write(r.content)

    return jsonify({
        "audioUrl": f"https://deepdub-vapi-proxy.onrender.com/audio/{filename}"
    })

@app.route("/audio/<filename>")
def serve_audio(filename):
    return send_from_directory(AUDIO_FOLDER, filename)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)