# Contributing to Plappo — how to work in this repo

Plappo is a German learning app: it gives you a **level-appropriate story**, asks
you to answer in your **own written German**, gives **focused grammar feedback**,
and schedules **spaced review** — adapting to a **measured** (not self-declared)
level. This file is the contract for anyone (human or AI) writing code here.

> **Read first:** [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) (how it fits
> together), [docs/DECISIONS.md](docs/DECISIONS.md) (why it's built this way),
> [docs/PEDAGOGY_ROADMAP.md](docs/PEDAGOGY_ROADMAP.md) (the learning science it
> serves).

## Engineering standards (the bar)

The goal is code an architect *and* an engineer are happy with — and **no big
refactors later**. That comes from a few non-negotiables:

1. **Respect the data contracts.** Three shapes are load-bearing and stable:
   `TutorFeedback` (grammar feedback), the **story object** (title/sentences/
   glossary/questions/check/tags), and the **profile** (skills + vocab + goal).
   Changing them ripples everywhere — extend additively, never repurpose a field.
2. **One source of truth.** The error `taxonomy.py` is shared by the dataset, the
   model's output schema, the scorer, and the UI. Add a category there and only
   there. Don't hardcode category lists anywhere else.
3. **Separation of concerns — keep these boundaries clean:**
   - *Engine vs UI:* grammar judgment lives server-side (`vertex_backend` /
     `tutor`), never in the browser. The UI renders, it doesn't decide.
   - *Generation vs selection:* generating content (expensive, LLM) is separate
     from choosing content for a user (cheap, ranking). See ADR-013.
   - *Offline eval vs runtime:* rigorous measurement (Pro judge, full datasets)
     is separate from the lightweight in-app guard (Flash). Don't conflate them.
   - *Provider boundary:* every LLM call goes through `vertex_backend.py`. Swapping
     model/provider must touch *only* that file.
4. **Never burn LLM credit in the request path** when you can avoid it. Cache,
   reuse the library, batch offline. A user opening a story should usually hit the
   corpus, not a generation call (ADR-013, ADR-016).
5. **Validate before you build.** The spine of this project is: prove the risky
   thing with an eval *first* (the feedback engine, then story-in-level), then build
   UI on top. New risky capability → new eval before new UI.
6. **Design for the documented roadmap, not hypothetical futures.** Don't
   over-abstract. But don't paint into corners either — the story library is the
   model: ship the forward-compatible *data shape* now, add the selector later
   (ADR-013). When in doubt, make the data right and keep the logic simple.
7. **Comments explain _why_, not _what_.** The code says what. Comments carry the
   rationale, the pedagogy link, the caveat. Match the surrounding style.
8. **Be honest in code and docs.** Label simplifications (`FSRS-style`, not
   "FSRS"), note caveats, don't claim more than the evals measured.

## Anti-patterns (do not do)

- Putting grammar/level logic in the UI, or duplicating the taxonomy in JS as
  truth (the JS `CAT` map is presentation metadata only — labels/colours).
- A schema change that renames/repurposes an existing field instead of adding one.
- Generating content synchronously in the request path when the library could serve it.
- "Improving" a number past what the eval measured, or removing a caveat.
- Over-engineering for a future the roadmap doesn't list.

## Where things live

```
eval/          offline measurement + the LLM service layer (the "truth")
  taxonomy.py        single source of error categories
  dataset.py         gold grammar cases (A1–C2)
  tutor.py           the feedback prompt + TutorFeedback schema
  vertex_backend.py  the ONLY place that talks to the LLM (Gemini on Vertex)
  score.py           grammar metrics
  run_compare.py     Pro-vs-Flash grammar eval
  story_level_eval.py story-in-level (drift) eval
  story_service.py   gated story generation + the on-disk library
  vocab_coverage.py  deterministic per-level lexical-coverage gate (ADR-019)
  build_vocab_bands.py  one-time bootstrap of data/vocab_bands.json
  library/stories.json   the growing story corpus
  data/vocab_bands.json  per-level allowed vocabulary (bootstrap approximation)
prototype/     the runnable app
  server.py          stdlib server: /api/feedback, /api/story (reuses eval/)
  index.html         the whole single-page UI (no build step)
docs/          architecture, decisions, pedagogy
```

## How to extend (common tasks)

- **Add an error category:** add it to `taxonomy.py` (enum + hint). The model
  schema, scorer, and tutor prompt pick it up automatically. Add a label/colour to
  the JS `CAT` map and, if it's a level-defining skill, to `LEVELCFG`.
- **Add grammar test cases:** append `Case(...)` rows to `dataset.py`. Keep ~half
  already-correct (they drive the false-positive metric — the trust metric).
- **Add a CEFR level's grammar:** edit `LEVELCFG` (prototype) — the level→skill
  mapping. Validate it against a real syllabus; it's a heuristic (ADR-007).
- **Change the model/provider:** edit `vertex_backend.py` only.
- **Run the evals:** see `eval/README.md` (grammar: `run_compare.py`; stories:
  `story_level_eval.py`). Both need `gcloud auth application-default login`.

## Constraints

- LLM is **Gemini on Vertex** via GCP ADC. The engine is provider-isolated, so
  swapping model or provider is a one-file concern (`vertex_backend.py`, ADR-005).
- Vertex config (`VERTEX_PROJECT` / `VERTEX_LOCATION`) is read from process env or
  a local `.env` (path overridable via `VERTEX_ENV`). The `.env` is never committed.
- Credit-conscious: prefer library/cache; the offline evals are where you spend
  for rigour. Use the Batch API for bulk offline generation when you build it.
