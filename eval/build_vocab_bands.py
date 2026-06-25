"""One-time bootstrap of per-level German vocabulary bands (ADR-019).

Produces `data/vocab_bands.json`: for each CEFR level, the cumulative set of
allowed lemmas. The lexical-coverage gate uses this to decide, deterministically,
whether a generated story stays within its level's vocabulary.

HONEST CAVEAT: these bands are *bootstrapped from the LLM*, not an authoritative
Goethe / corpus frequency list — they're a usable approximation so the gate is
real and deterministic *today*. Swap in a proper list to improve quality without
changing any calling code. Run once; commit the JSON.

    python build_vocab_bands.py
"""

import json
import os

from vertex_backend import vertex_json

# Roughly how many *new* lemmas each level introduces. Kept modest per call so the
# JSON array never overruns the token budget; quality matters more than exact size.
LEVELS = [("A1", 350), ("A2", 300), ("B1", 350), ("B2", 350), ("C1", 350), ("C2", 350)]
SCHEMA = {"type": "OBJECT", "properties": {"lemmas": {"type": "ARRAY", "items": {"type": "STRING"}}},
          "required": ["lemmas"]}


def fetch_level(level, k, already):
    sys = ("You are a German corpus lexicographer. Return common German LEMMAS (base "
           "forms, lowercase: nouns without article, verbs as infinitive, adjectives "
           "uninflected). High-frequency, everyday words a learner meets — including "
           "function words at A1.")
    user = (f"List about {k} common German lemmas typical of CEFR level {level} that are "
            f"NOT already in this list: {', '.join(sorted(already)[:120])}{'…' if len(already)>120 else ''}.\n"
            f"Return lemmas only, base form, lowercase.")
    try:
        out = vertex_json("gemini-2.5-flash", sys, user, SCHEMA, temperature=0.3,
                          max_tokens=32768, thinking_budget=0)  # no thinking -> full output
    except Exception as e:  # noqa: BLE001 — tolerate an occasional bad/truncated batch
        print(f"  ! {level}: batch failed ({type(e).__name__}); continuing")
        return []
    return [w.strip().lower() for w in out.get("lemmas", []) if w.strip()]


def main():
    bands, cumulative = {}, set()
    for level, k in LEVELS:
        new = fetch_level(level, k, cumulative)
        cumulative |= set(new)
        bands[level] = sorted(cumulative)
        print(f"{level}: +{len(new)} new -> {len(cumulative)} cumulative")
    out_dir = os.path.join(os.path.dirname(__file__), "data")
    os.makedirs(out_dir, exist_ok=True)
    path = os.path.join(out_dir, "vocab_bands.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(bands, f, ensure_ascii=False, indent=1)
    print(f"\nwrote {path}")


if __name__ == "__main__":
    main()
