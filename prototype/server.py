"""Tiny local server for the Plappo prototype.

Serves the single-page UI and proxies grammar-feedback requests to the
Gemini-on-Vertex backend we already built and validated in ../eval. The browser
never sees the Vertex token — it just POSTs {level, sentence} here.

    python server.py            # http://127.0.0.1:8000
    PLAPPO_MODEL=gemini-2.5-pro python server.py
"""

import json
import os
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

# Reuse the validated Vertex backend from the eval harness.
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "eval"))
from vertex_backend import VertexGeminiTutor  # noqa: E402

HERE = os.path.dirname(__file__)
MODEL = os.environ.get("PLAPPO_MODEL", "gemini-2.5-flash")
PORT = int(os.environ.get("PLAPPO_PORT", "8000"))

_tutor = None


def tutor():
    global _tutor
    if _tutor is None:
        _tutor = VertexGeminiTutor(MODEL)
    return _tutor


class Handler(BaseHTTPRequestHandler):
    def _send(self, code, body, ctype="application/json"):
        data = body if isinstance(body, bytes) else body.encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        path = "index.html" if self.path in ("/", "") else self.path.lstrip("/")
        full = os.path.normpath(os.path.join(HERE, path))
        if not full.startswith(HERE) or not os.path.isfile(full):
            return self._send(404, "not found", "text/plain")
        ctype = "text/html" if full.endswith(".html") else "text/plain"
        with open(full, "rb") as f:
            self._send(200, f.read(), ctype)

    def do_POST(self):
        try:
            n = int(self.headers.get("Content-Length", 0))
            req = json.loads(self.rfile.read(n) or b"{}")
            if self.path == "/api/feedback":
                level = req.get("level", "A2")
                sentence = (req.get("sentence") or "").strip()
                if not sentence:
                    return self._send(400, json.dumps({"error": "empty sentence"}))
                fb = tutor().get_feedback(level, sentence)
                out = fb.model_dump(mode="json")
                # Attach the deterministic content-vocabulary classification so the
                # client measures the vocab axis from content lemmas, not raw tokens
                # (P2). No extra LLM call.
                try:
                    from vocab_coverage import classify_vocab
                    out["content_lemmas"] = [v["lemma"] for v in classify_vocab(sentence)]
                except Exception:  # noqa: BLE001 — vocab is a nicety, never block feedback
                    out["content_lemmas"] = []
                return self._send(200, json.dumps(out, ensure_ascii=False))
            if self.path == "/api/story":
                from story_service import (generate_gated_story, save_to_library,
                                           select_from_library)
                level = req.get("level", "A2")
                topic = (req.get("topic") or "ein Tag in der Stadt").strip()
                prefer = req.get("prefer", "library")
                # generate once, add as you go: serve from the shared corpus when
                # possible (cheap, no LLM call); only generate on a miss or a
                # "fresh" request, then persist the result for everyone.
                if prefer != "fresh":
                    cached = select_from_library(level)
                    if cached:
                        cached["source"] = "library"
                        return self._send(200, json.dumps(cached, ensure_ascii=False))
                story = generate_gated_story(level, topic)
                save_to_library(story)
                return self._send(200, json.dumps(story, ensure_ascii=False))
            return self._send(404, json.dumps({"error": "not found"}))
        except Exception as e:  # noqa: BLE001
            self._send(500, json.dumps({"error": str(e)}))

    def log_message(self, fmt, *args):
        if self.path == "/api/feedback":
            sys.stderr.write("  feedback call -> %s\n" % (args[1] if len(args) > 1 else ""))


if __name__ == "__main__":
    print(f"Plappo prototype on http://127.0.0.1:{PORT}   (model: {MODEL})")
    print("Open that URL in your browser. Ctrl-C to stop.")
    ThreadingHTTPServer(("127.0.0.1", PORT), Handler).serve_forever()
