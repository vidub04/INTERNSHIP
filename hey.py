#!/usr/bin/env python3
import os, requests
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS

app = Flask(__name__, static_folder="static")
CORS(app)

API_KEY ="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"
MODEL   = "mistralai/mistral-7b-instruct"


SYSTEM_ROLE = (
    "You are Findash- a financial assistant. Answer all the queries in simple English, understandable to all." 
    "You must answer in a formal tone, disclosing you are not a licensed agent. "
)

PROMPTS = {
    "joke":    "Tell me a money‑related joke.",
    "haiku":   "Write a haiku about compound interest.",
    "summary": "Summarise the concept of an ETF in two sentences."
}

def call_openrouter(prompt: str) -> str:
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "HTTP-Referer": "https://localhost",
        "Content-Type": "application/json"
    }
    payload = {
        "model": MODEL,
        "messages": [
            {"role": "system", "content": SYSTEM_ROLE},   # ②  ADD ROLE HERE
            {"role": "user",   "content": prompt}
        ]
    }
    r = requests.post("https://openrouter.ai/api/v1/chat/completions",
                      json=payload, headers=headers, timeout=30)
    r.raise_for_status()
    return r.json()["choices"][0]["message"]["content"]

@app.route("/chat", methods=["POST"])
def chat():
    option = request.json.get("option")
    prompt = PROMPTS.get(option)
    if not prompt:
        return jsonify(error="invalid option"), 400
    try:
        return jsonify(reply=call_openrouter(prompt))
    except requests.HTTPError as e:
        return jsonify(error="OpenRouter error", detail=e.response.text), 502

@app.route("/", defaults={"path": "index.html"})
@app.route("/<path:path>")
def static_files(path):
    return send_from_directory(app.static_folder, path)

if __name__ == "__main__":
    app.run(debug=True)
