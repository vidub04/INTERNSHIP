#!/usr/bin/env python3
"""
Flask → OpenRouter bridge for an Excel/JS add‑in
Run with:  python main.py   (defaults to http://127.0.0.1:5000)
"""

import os
import json
import requests
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from dotenv import load_dotenv

load_dotenv()                                      # pulls .env in dev

API_KEY = os.getenv("OPENROUTER_API_KEY")
if not API_KEY:
    raise RuntimeError(
        "OPENROUTER_API_KEY not set. "
        "Put it in your environment or .env file."
    )

MODEL = "mistralai/mistral-7b-instruct"            # any OpenRouter model

app = Flask(__name__, static_folder="static")
CORS(app)                                          # very open – restrict in prod!

# ──────────────────────────────────────────────────────────────
# 3.  System role for every chat
# ──────────────────────────────────────────────────────────────
SYSTEM_ROLE = (
    "You are Findash – a financial assistant. Answer queries in simple, formal "
    "English that a non‑specialist can understand. Disclose you are not a "
    "licensed agent. If you don't know the answer, reply: "
    "\"I am unable to process your query at the moment. Please try rephrasing "
    "or asking a different question.\""
)

PROMPTS = {
    "summary":
        "Provide a concise portfolio summary, including:\n"
        "• General overview\n• Asset allocation\n• Valuation estimate\n• "
        "Benchmark comparison\n\nDataset:\n{table}",
    "allocation":
        "Analyze the asset allocation in the following data. Highlight any "
        "over‑ or under‑exposure:\n{table}",
    "valuation":
        "Estimate the portfolio's valuation based on this data. Explain your "
        "method briefly:\n{table}",
    "benchmark":
        "Compare this portfolio against an appropriate benchmark. Point out "
        "areas of over‑ or under‑performance:\n{table}",
    "performance":
        "Create a performance breakdown for the period reflected below:\n{table}",
    "trend":
        "Perform a trend analysis on the following dataset:\n{table}",
    "forecast":
        "Forecast portfolio performance for the next 12 months using the "
        "historic data:\n{table}",
    "kpi":
        "Extract key performance indicators (KPIs) from this table and discuss "
        "them:\n{table}",
    "risk":
        "Assess the portfolio's risk exposure, citing metrics such as "
        "volatility and max drawdown, based on this data:\n{table}",
    "ratios":
        "Compute and interpret relevant financial ratios (e.g., Sharpe, "
        "Sortino) using this dataset:\n{table}",
    "cashflow":
        "Perform a cash‑flow analysis highlighting inflows, outflows, and net "
        "position:\n{table}",
    
    "improvements":
        "Suggest actionable improvements or optimisations for the portfolio "
        "below:\n{table}",
}


def call_openrouter(prompt: str) -> str:
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "HTTP-Referer": "https://localhost",    # optional – per OR docs
        "Content-Type": "application/json",
    }
    payload = {
        "model": MODEL,
        "messages": [
            {"role": "system", "content": SYSTEM_ROLE},
            {"role": "user",   "content": prompt},
        ],
    }
    r = requests.post(
        "https://openrouter.ai/api/v1/chat/completions",
        json=payload,
        headers=headers,
        timeout=45,
    )
    r.raise_for_status()
    return r.json()["choices"][0]["message"]["content"].strip()
    
@app.route("/chat", methods=["POST"])
def chat():
    """
    Expected JSON:
        {
          "option": "summary",          # dropdown option key
          "data":   [[...], [...]],     # 2‑D array from Excel
          "address": "A1:B10"           # optional range info
        }
    """
    body = request.get_json(force=True)
    option  = (body or {}).get("option")
    data_2d = (body or {}).get("data")

    # validate
    if option not in PROMPTS:
        return jsonify(error="invalid option key"), 400
    if not isinstance(data_2d, list):
        return jsonify(error="data must be a 2‑D array"), 400

    table = json.dumps(data_2d, indent=2)
    user_prompt = PROMPTS[option].format(table=table)

    try:
        reply = call_openrouter(user_prompt)
        return jsonify(reply=reply, address=body.get("address"))
    except requests.HTTPError as e:
        return jsonify(error="OpenRouter error", detail=e.response.text), 502

# ──────────────────────────────────────────────────────────────
# 7.  Serve static task‑pane files if you keep them here
# ──────────────────────────────────────────────────────────────
@app.route("/", defaults={"path": "index.html"})
@app.route("/<path:path>")
def static_files(path):
    return send_from_directory(app.static_folder, path)


if __name__ == "__main__":

    app.run(debug=True, port=5000)
