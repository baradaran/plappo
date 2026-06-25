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
`PLAPPO_MODEL=gemini-2.5-pro python server.py`.

## The flow

1. **Home** — pick a level; see your "weak spots" (fills in as you make mistakes).
2. **Story** — read an A2 story; tap any word for a gloss; harder words are highlighted.
3. **Questions** — type a free German answer, hit **Prüfen**. This calls the real
   grammar engine and renders the **feedback card**: your sentence with the wrong
   bits struck through, a coloured chip per error (category + fix + explanation),
   and the corrected sentence.
4. **Drill it** — generates a tap-to-order mini-exercise targeting the error
   category you just made.

## How it's wired

- `server.py` — stdlib HTTP server. Serves `index.html`; `POST /api/feedback`
  `{level, sentence}` calls `../eval/vertex_backend.py` and returns the same
  `TutorFeedback` JSON the eval scores. **The Vertex token never reaches the browser.**
- `index.html` — the whole UI (no build step, no dependencies). Category colours,
  the feedback renderer, and the weak-spots chart all read the engine's fields
  directly.

## What's real vs. stubbed

| Real | Stubbed (prototype) |
|---|---|
| Grammar feedback (live Gemini) | The story (one hardcoded A2 text) |
| Error categories, corrections, explanations | Comprehension questions (3 fixed) |
| Weak-spot aggregation from your answers | Drills (a few hardcoded per category) |
| | Streak / XP / SRS scheduling |

The story-generation and drill-generation would themselves be model calls in the
real app — and story generation (staying inside a CEFR level) is the next
unsolved problem to test, separate from the feedback engine this validates.
