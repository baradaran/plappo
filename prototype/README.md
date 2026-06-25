# Plappo — clickable prototype

A 4-screen walkthrough of the app, with the **feedback card wired to live
Gemini 2.5 Flash** on Vertex AI.

## Run

```bash
# needs a gcloud ADC login (gcloud auth application-default login)
cd prototype
python server.py            # -> http://127.0.0.1:8000
```

Open <http://127.0.0.1:8000> in a browser. Use Gemini Pro instead:
`PLAPPO_MODEL=gemini-2.5-pro python server.py`. Append `?demo=1` to the URL to load
populated demo data (streak/skills/reviews) for screenshots; without it you get an
honest zero-state first run.

> **Display note:** the UI is intentionally a **412 px phone-frame mock**, centred
> on desktop — it is not a responsive web layout. Best viewed narrow (or in a
> browser device emulator).

## The flow

1. **Home** — your level is *measured*, not picked; weak spots fill in as you write.
2. **Story** — read a level-appropriate story (generated and in-band-gated server-
   side, served from a growing library); tap any word for a quiet gloss — an
   ephemeral reading aid. Meaning is never trained: this app trains **grammar**,
   and a lookup only signals "unknown word" (ADR-018/020/021).
3. **Questions** — type a free German answer, hit **Check my German**. This calls
   the real grammar engine and renders the **feedback card**: your sentence with the
   wrong bit struck through (with the fix), one focused error chip (the rest collapse),
   praise that names a strength you actually showed, and the corrected sentence. The
   error also becomes a spaced-review card.
4. **Drill it** — a tap-to-order exercise built from *your own corrected sentence*.

## How it's wired

- `server.py` — stdlib HTTP server. Serves `index.html`; `POST /api/feedback`
  `{level, sentence}` calls `../eval/vertex_backend.py` and returns the same
  `TutorFeedback` JSON the eval scores. **The Vertex token never reaches the browser.**
- `index.html` — the whole UI (no build step, no dependencies). Category colours,
  the feedback renderer, and the weak-spots chart all read the engine's fields
  directly.

## What's real vs. stubbed

| Real | Stubbed / simplified (prototype) |
|---|---|
| Grammar feedback (live Gemini) | Comprehension questions (fixed per story) |
| Error categories, corrections, explanations | Goal/streak gamification |
| Level + vocab **measured** from your writing (skills only credited when exercised; vocab from content lemmas) | Persistence is `localStorage` |
| Story generation, in-band gated, served from a library (with offline fallback) | |
| Spaced review (**real FSRS-5**) with **typed, verified** recall | |
| Drills + review cards built from your real mistakes | |

Story generation staying inside a CEFR level is validated separately by the
story-level eval (`../eval/story_level_eval.py`); the `demonstrated`-skills signal
that drives the measured level has its own gate (`../eval/skills_demonstrated_eval.py`).
