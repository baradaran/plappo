"""Gemini-on-Vertex backend for the tutor.

This backend lets the SAME eval (same prompt, same schema, same dataset, same
scorer) run against Gemini 2.5 Pro / Flash, so the numbers are comparable to a
future Claude run.

Auth + config:
  - VERTEX_PROJECT / VERTEX_LOCATION from process env, or a local .env file
    (path overridable via VERTEX_ENV; defaults to ../.env)
  - bearer token via `gcloud auth application-default print-access-token` (ADC)

Note this evaluates GEMINI, not Claude — see README. It's a deliberate,
user-directed departure from the Claude SDK because that's where the credit is.
"""

import json
import os
import subprocess
import time
import urllib.error
import urllib.request

from taxonomy import ErrorCategory
from tutor import SYSTEM_PROMPT, TutorFeedback

# Where to find Vertex config (VERTEX_PROJECT/VERTEX_LOCATION) if it's not
# already in the environment. Override the path with VERTEX_ENV.
_VERTEX_ENV = os.environ.get(
    "VERTEX_ENV",
    os.path.join(os.path.dirname(__file__), "..", ".env"),
)

_token_cache = {"token": "", "exp": 0.0}


def _load_dotenv_value(path, key):
    try:
        with open(path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line.startswith(key + "="):
                    return line.split("=", 1)[1].strip().strip('"').strip("'")
    except OSError:
        pass
    return None


def vertex_config():
    project = os.environ.get("VERTEX_PROJECT") or _load_dotenv_value(_VERTEX_ENV, "VERTEX_PROJECT")
    location = (os.environ.get("VERTEX_LOCATION")
                or _load_dotenv_value(_VERTEX_ENV, "VERTEX_LOCATION") or "global")
    if not project:
        raise RuntimeError("VERTEX_PROJECT not found (env or .env).")
    return project, location


def _adc_token():
    now = time.time()
    if _token_cache["token"] and _token_cache["exp"] > now + 120:
        return _token_cache["token"]
    gcloud = "gcloud.cmd" if os.name == "nt" else "gcloud"
    out = subprocess.run(
        [gcloud, "auth", "application-default", "print-access-token"],
        capture_output=True, text=True, timeout=30,
    )
    if out.returncode != 0:
        raise RuntimeError(f"gcloud ADC token failed: {out.stderr.strip()}")
    tok = out.stdout.strip()
    _token_cache.update(token=tok, exp=now + 3000)  # tokens last ~1h; refresh at 50m
    return tok


# Gemini responseSchema (OpenAPI subset; types are UPPERCASE). Mirrors
# tutor.TutorFeedback so both backends are scored identically.
_RESPONSE_SCHEMA = {
    "type": "OBJECT",
    "properties": {
        "has_errors": {"type": "BOOLEAN"},
        "corrected_sentence": {"type": "STRING"},
        "errors": {
            "type": "ARRAY",
            "items": {
                "type": "OBJECT",
                "properties": {
                    "category": {"type": "STRING", "enum": [c.value for c in ErrorCategory]},
                    "original_fragment": {"type": "STRING"},
                    "correction": {"type": "STRING"},
                    "explanation": {"type": "STRING"},
                },
                "required": ["category", "original_fragment", "correction", "explanation"],
            },
        },
        # Constructions the learner used correctly (additive; see tutor.TutorFeedback).
        # Not required, so the model may return [] when nothing was clearly exercised.
        "demonstrated": {
            "type": "ARRAY",
            "items": {"type": "STRING", "enum": [c.value for c in ErrorCategory]},
        },
    },
    "required": ["has_errors", "corrected_sentence", "errors"],
}


class VertexGeminiTutor:
    """Engine with the same get_feedback(level, sentence) -> TutorFeedback shape
    used by the rest of the harness."""

    def __init__(self, model_id):
        self.model_id = model_id.split("/")[-1]  # "google/gemini-2.5-pro" -> "gemini-2.5-pro"
        self.project, self.location = vertex_config()
        host = ("aiplatform.googleapis.com" if self.location == "global"
                else f"{self.location}-aiplatform.googleapis.com")
        self.endpoint = (
            f"https://{host}/v1/projects/{self.project}"
            f"/locations/{self.location}/publishers/google/models/{self.model_id}:generateContent"
        )

    def get_feedback(self, level, sentence) -> TutorFeedback:
        body = {
            "systemInstruction": {"parts": [{"text": SYSTEM_PROMPT}]},
            "contents": [{"role": "user",
                          "parts": [{"text": f"Learner level: {level}\nSentence: {sentence}"}]}],
            "generationConfig": {
                "temperature": 0,
                "maxOutputTokens": 16384,  # headroom for Gemini 2.5 Pro thinking tokens
                "responseMimeType": "application/json",
                "responseSchema": _RESPONSE_SCHEMA,
            },
        }
        data = self._post(body)
        text = self._extract_json_text(data)
        if not text:
            # Empty (e.g. thinking ate the token budget) — treat as no usable feedback.
            return TutorFeedback(has_errors=False, corrected_sentence=sentence, errors=[])
        parsed = json.loads(text)
        return TutorFeedback.model_validate(parsed)

    def _post(self, body):
        req = urllib.request.Request(
            self.endpoint,
            data=json.dumps(body).encode("utf-8"),
            headers={"Authorization": f"Bearer {_adc_token()}",
                     "Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=120) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            detail = e.read().decode("utf-8", "replace")[:500]
            raise RuntimeError(f"Vertex HTTP {e.code} for {self.model_id}: {detail}") from None

    @staticmethod
    def _extract_json_text(data):
        cands = data.get("candidates") or []
        if not cands:
            return ""
        parts = (cands[0].get("content") or {}).get("parts") or []
        # Skip "thought" parts (Gemini 2.5 thinking); keep the answer text.
        answer = [p.get("text", "") for p in parts if "text" in p and not p.get("thought")]
        text = "".join(answer) or "".join(p.get("text", "") for p in parts if "text" in p)
        text = text.strip()
        if text.startswith("```"):  # strip accidental code fences
            text = text.strip("`")
            if text.lstrip().lower().startswith("json"):
                text = text.lstrip()[4:]
        return text.strip()


# --- generic structured-generation helper (used by the story-level eval) ------
def _model_endpoint(model_id):
    project, location = vertex_config()
    host = ("aiplatform.googleapis.com" if location == "global"
            else f"{location}-aiplatform.googleapis.com")
    return (f"https://{host}/v1/projects/{project}/locations/{location}"
            f"/publishers/google/models/{model_id.split('/')[-1]}:generateContent")


def vertex_json(model_id, system, user, response_schema, temperature=0.6, max_tokens=8192,
                thinking_budget=None):
    """One structured (JSON-schema-constrained) generation. Returns a parsed dict.
    Pass thinking_budget=0 on Flash to disable thinking (all tokens go to output) —
    useful for long bulk outputs that would otherwise be truncated."""
    gen_cfg = {"temperature": temperature, "maxOutputTokens": max_tokens,
               "responseMimeType": "application/json", "responseSchema": response_schema}
    if thinking_budget is not None:
        gen_cfg["thinkingConfig"] = {"thinkingBudget": thinking_budget}
    body = {
        "systemInstruction": {"parts": [{"text": system}]},
        "contents": [{"role": "user", "parts": [{"text": user}]}],
        "generationConfig": gen_cfg,
    }
    req = urllib.request.Request(
        _model_endpoint(model_id), data=json.dumps(body).encode("utf-8"),
        headers={"Authorization": f"Bearer {_adc_token()}", "Content-Type": "application/json"},
        method="POST")
    try:
        with urllib.request.urlopen(req, timeout=180) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        raise RuntimeError(f"Vertex HTTP {e.code} for {model_id}: "
                           f"{e.read().decode('utf-8','replace')[:400]}") from None
    text = VertexGeminiTutor._extract_json_text(data)
    return json.loads(text) if text else {}
