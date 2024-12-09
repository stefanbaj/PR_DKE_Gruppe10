import openai
import os
from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv

# Lade Umgebungsvariablen
load_dotenv()

app = Flask(__name__)
CORS(app)

# Setze den API-Schlüssel
openai.api_key = os.getenv("OPENAI_API_KEY")

@app.route("/chat", methods=["POST"])
def chat():
    data = request.json
    message = data.get("message")

    if not message:
        return jsonify({"error": "Message is required"}), 400

    try:
        # Korrekte Methode für neuere API-Versionen
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": message}],
            max_tokens=100
        )
        reply = response['choices'][0]['message']['content']  # Antwort extrahieren
        return jsonify({"reply": reply})
    except Exception as e:
        print("Error in chat:", e)
        return jsonify({"error": "Failed to generate response"}), 500

if __name__ == "__main__":
    port = int(os.getenv("PORT", 3000))
    app.run(host="0.0.0.0", port=port)
