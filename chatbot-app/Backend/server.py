# openai imports
import os
from flask import Flask, request, jsonify
from openai import OpenAI, OpenAIError
from flask_cors import CORS

# Config
app = Flask(__name__)
CORS(app)
openai = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Define route for chat
@app.route("/chat", methods=["POST"])
def chat():
    data = request.json
    message = data.get("message")

    if not message:
        return jsonify({"error": "Message is required"}), 400

    # Limit tokens per response
    MAX_TOKENS_PER_RESPONSE = 100

    try:
        # Generate OpenAI response with token limit
        completion = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",  # Specify model
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": message},
            ],
            max_tokens=MAX_TOKENS_PER_RESPONSE  # Limit the number of tokens in the response
        )

        reply = completion.choices[0].message["content"]
        tokens_used = completion["usage"]["completion_tokens"]  # Get tokens used for the reply

        return jsonify({"reply": reply, "tokens_used": tokens_used})

    except OpenAIError as e:
        print("Error in chat:", e)
        return "Error generating response", 500

# Start server
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 3000))
    app.run(host="0.0.0.0", port=port)
