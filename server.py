#!/usr/bin/env python3
"""
Robot brain (runs on your PC)
-----------------------------
The face lives on GitHub Pages. This takes what you say, gets a reply from Ollama
on this PC, turns it into a voice with the free Microsoft Edge voices, and sends it back.

  1. Once:  pip install --user --break-system-packages edge-tts
  2. Run:   python3 server.py
  3. Once, in another window:  sudo tailscale funnel --bg 8000

The passcode lives in passcode.txt next to this file. It's made for you the first
time you run this, and it never goes on GitHub.
"""

import asyncio
import base64
import json
import re
import secrets
import threading
import urllib.error
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

try:
    import edge_tts
except ImportError:
    edge_tts = None

# ─────────────────────────────── Settings ───────────────────────────────
PORT = 8000
OLLAMA_URL = "http://localhost:11434"
DEFAULT_MODEL = ""                         # Used when customize.js leaves aiModel empty. Empty = first installed model
SITE_URL = "https://itzcatto.github.io/rooomba/"

DEFAULT_VOICE = "en-AU-WilliamNeural"      # Australian guy (customize.js can override)
DEFAULT_PERSONA = "You are the sarcastic, rude AI inside a robot vacuum. Reply in one to three short sentences."

PASSCODE_FILE = Path(__file__).with_name("passcode.txt")


def load_passcode():
    if PASSCODE_FILE.exists():
        return PASSCODE_FILE.read_text().strip()
    code = secrets.token_urlsafe(9)
    PASSCODE_FILE.write_text(code + "\n")
    return code


def ollama(path, data=None, timeout=180):
    body = json.dumps(data).encode() if data is not None else None
    req = urllib.request.Request(OLLAMA_URL + path, data=body, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.load(r)


def think(messages, model):
    payload = {"model": model or DEFAULT_MODEL, "messages": messages, "stream": False, "keep_alive": "1h"}
    try:
        result = ollama("/api/chat", payload)
    except urllib.error.HTTPError as e:
        if e.code != 404 or payload["model"] == DEFAULT_MODEL:
            raise
        print(f"Model '{payload['model']}' isn't installed, using {DEFAULT_MODEL} instead.")
        result = ollama("/api/chat", {**payload, "model": DEFAULT_MODEL})
    reply = result["message"]["content"]
    return re.sub(r"<think>.*?</think>", "", reply, flags=re.S).strip()   # some models think out loud first


def voice(text, voice_name, rate, pitch):
    """Turn text into mp3 audio. Returns None if it fails, so the tablet uses its own voice."""
    if not text or not edge_tts:
        return None

    async def speak():
        audio = b""
        async for chunk in edge_tts.Communicate(text, voice_name, rate=rate, pitch=pitch).stream():
            if chunk["type"] == "audio":
                audio += chunk["data"]
        return audio

    try:
        return asyncio.run(speak()) or None
    except Exception as e:
        print(f"Voice error: {e}")
        return None


def clean(value, default, pattern):
    value = str(value or "").strip()
    return value if re.fullmatch(pattern, value) else default


class Handler(BaseHTTPRequestHandler):
    def cors(self):
        # The face is on GitHub Pages, a different site, so the browser needs permission to talk to this PC
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, x-robot-key")
        self.send_header("Access-Control-Allow-Private-Network", "true")
        self.send_header("Access-Control-Max-Age", "600")

    def send_json(self, code, data):
        body = json.dumps(data).encode()
        self.send_response(code)
        self.cors()
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self):
        self.send_response(204)
        self.cors()
        self.send_header("Content-Length", "0")
        self.end_headers()

    def do_GET(self):
        if self.path.split("?")[0] == "/api/health":
            self.send_json(200, {"robot": True})
        else:
            self.send_json(404, {"error": "not found"})

    def do_POST(self):
        if self.path.split("?")[0] != "/api/chat":
            return self.send_json(404, {"error": "not found"})
        if PASSCODE and self.headers.get("x-robot-key", "") != PASSCODE:
            return self.send_json(401, {"error": "wrong passcode"})
        try:
            length = int(self.headers.get("Content-Length", 0))
            body = json.loads(self.rfile.read(length) or b"{}")
            text = str(body.get("text", "")).strip()[:1000]
        except (ValueError, AttributeError):
            return self.send_json(400, {"error": "bad request"})
        if not text:
            return self.send_json(400, {"error": "no text"})

        history = [
            {"role": m["role"], "content": m["content"][:2000]}
            for m in (body.get("history") or [])[-40:]
            if isinstance(m, dict) and m.get("role") in ("user", "assistant") and isinstance(m.get("content"), str)
        ]
        persona = str(body.get("prompt") or "").strip()[:8000] or DEFAULT_PERSONA
        messages = [{"role": "system", "content": persona}] + history + [{"role": "user", "content": text}]

        print(f"You:   {text}")
        try:
            reply = think(messages, str(body.get("model") or "").strip())
        except (urllib.error.URLError, OSError, KeyError, ValueError) as e:
            print(f"Ollama error: {e}")
            return self.send_json(502, {"error": str(e)})

        voice_name = clean(body.get("voice"), DEFAULT_VOICE, r"[a-z]{2,3}-[A-Z]{2}-[A-Za-z]+Neural")
        rate = clean(body.get("voiceSpeed"), "+0%", r"[+-]\d{1,3}%")
        pitch = clean(body.get("voicePitch"), "+0Hz", r"[+-]\d{1,3}Hz")
        audio = voice(re.sub(r"\[eye ?roll\]", "", reply, flags=re.I).strip(), voice_name, rate, pitch)
        print(f"Robot: {reply}" + ("" if audio else "  (using the tablet's own voice)") + "\n")
        self.send_json(200, {"reply": reply, "audio": base64.b64encode(audio).decode() if audio else None})

    def log_message(self, *args):
        pass   # keep the console tidy


def warm_up():
    try:
        ollama("/api/generate", {"model": DEFAULT_MODEL, "keep_alive": "1h"}, timeout=300)
        print("Model loaded and ready.\n")
    except Exception as e:
        print(f"Couldn't preload the model ({e}). The first reply may be slow.\n")


if __name__ == "__main__":
    try:
        models = [m["name"] for m in ollama("/api/tags", timeout=5).get("models", [])]
    except Exception:
        raise SystemExit("Can't reach Ollama. Make sure it's running (open the Ollama app, or run: ollama serve).")
    if not models:
        raise SystemExit("No models installed yet. Run:  ollama pull llama3.2")
    if not DEFAULT_MODEL:
        DEFAULT_MODEL = models[0]
    PASSCODE = load_passcode()

    print(f"Brain running on port {PORT}, using {DEFAULT_MODEL}.")
    if not edge_tts:
        print("The voice isn't installed, so the tablet will use its own. To fix it, run:")
        print("  pip install --user --break-system-packages edge-tts\n")
    print(f"Tablet link (open it once):  {SITE_URL}?key={PASSCODE}\n")
    threading.Thread(target=warm_up, daemon=True).start()
    ThreadingHTTPServer(("0.0.0.0", PORT), Handler).serve_forever()
