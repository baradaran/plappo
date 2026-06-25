# Architecture

How Plappo is put together, the data contracts, and the runtime vs. offline split.
For *why* each choice was made, see [DECISIONS.md](DECISIONS.md).

## One-paragraph overview

A learner reads a **level-gated German story**, looks up words (which enter
**spaced repetition**), answers comprehension questions in **free-written German**,
and gets **focused grammar feedback** from an LLM. Every answer updates a
**measured** proficiency profile (grammar + vocabulary, tracked separately), which
sets the level of the next story. There are two halves — the **feedback engine**
(grades the learner's output) and the **content engine** (generates level-appropriate
input) — and each is validated by its own offline eval before it's trusted.

## Component map

```
                          ┌────────────────────────── OFFLINE (rigour) ──────────────────────────┐
                          │  run_compare.py        grammar feedback eval (Pro vs Flash)           │
                          │  story_level_eval.py   story-in-level drift eval (judge = Pro)         │
                          │  dataset.py / score.py / taxonomy.py                                   │
                          └───────────────────────────────────────────────────────────────────────┘
                                              shares the SAME code as runtime ↓

  Browser (index.html)            Server (server.py)                 LLM service layer (eval/)
  ┌───────────────────┐  POST     ┌──────────────────┐              ┌───────────────────────────┐
  │ Learn / Reader /  │ /feedback │ /api/feedback ───┼─────────────▶│ tutor.py  → TutorFeedback │
  │ Practice / Review │──────────▶│                  │              │ vertex_backend.py (Gemini)│
  │ / Profile         │  POST     │ /api/story:      │   library?   │ story_service.py:         │
  │                   │ /story    │  select_from_lib ├──hit──serve  │  generate_gated_story()   │
  │ profile + deck in │◀──────────│  else generate + │   miss│      │  + judge (story_level_eval)│
  │ localStorage      │   JSON    │       persist ───┼───────┴─────▶│ library/stories.json      │
  └───────────────────┘           └──────────────────┘              └───────────────────────────┘
```

Key point: the **server reuses the eval code** (`eval/` is on the server's path).
The thing we measured offline is the *same* thing that runs in production — no
drift between "what we tested" and "what ships".

## The provider boundary (one file)

Every LLM call — feedback, story generation, story judging — goes through
`eval/vertex_backend.py`. It owns: Gemini-on-Vertex endpoints, GCP ADC auth, the
structured-output plumbing, and the generic `vertex_json()` helper. Swapping model
or provider (e.g. to Claude, if a key appears) touches only this file. Nothing
upstream knows what model answered.

## Data contracts (stable — extend additively)

**`TutorFeedback`** (`tutor.py`) — grammar feedback:
```
{ has_errors: bool,
  corrected_sentence: str,
  errors: [ { category: <taxonomy enum>, original_fragment, correction, explanation } ] }
```

**Story object** (`story_service.py`) — generated input, also the library record:
```
{ id, level, topic, title, sentences: [str],
  glossary: [ { word, lemma, pos, en } ],
  questions: [str],
  grammar_points: [<taxonomy enum>],   theme: <enum>,     ← tags for selection
  check: { target, estimated, class: above|on|below, in_band, ... },
  created_at, gen_model, source: generated|library }
```

**Profile** (`index.html`, localStorage) — the learner:
```
{ level (working, DERIVED), goal, xp, streak, vocab, seenWords,
  skills: { <taxonomy enum>: 0..100 },        ← per-skill mastery
  encounters: { word: lookupCount },          ← ADR-021: "unknown word" signal
  known: { word: true }, seenNoLookup: { word: n },    ← carrier decay
  seen: [ storyId ] }                          ← ADR-013: don't re-serve stories
```

**Deck item** (FSRS) — one review card (grammar-only typed cloze, ADR-018):
```
{ id, type:"grammar", front:"… ___ …", answer, cat:<taxonomy>, expl, S, D, reps, last, due }
```

The error **taxonomy** (`taxonomy.py`, 20 categories) is the single source feeding
the `category` field in three of these. Add categories there only.

## Runtime vs. offline (deliberate asymmetry)

| | Offline eval | In-app runtime |
|---|---|---|
| Grammar | `run_compare.py` over `dataset.py`, scored | live `/api/feedback`, one sentence |
| Stories | `story_level_eval.py`, **judge = Pro** | `/api/story` gate, **judge = Flash** |
| Purpose | rigour, model comparison, regression | fast, cheap guard |
| Spend | where we pay for confidence | minimised (library/cache) |

## Level model (measured, not set)

Proficiency is two axes, both derived from data the app already collects:
- **Grammar level** = highest CEFR level whose skills are ≥66% mastered.
- **Vocabulary level** = band from cumulative words used.
- **Working level** (used for content + feedback) = first not-yet-solid level.
- **Goal** = the only thing the user sets.

CEFR explicitly allows such "jagged" profiles (e.g. *Grammar A1 · Vocabulary A2*).
See [PEDAGOGY_ROADMAP.md](PEDAGOGY_ROADMAP.md) and ADR-009.

## Story content: generate once, select per user, add as you go

The scalable shape (ADR-013): generation is expensive + shared across users +
risky (drift), so it runs **once** and the result is **persisted to a shared
library**; per-read **selection** is cheap. Three tiers:

```
client per-level cache  →  shared library (select_from_library)  →  generate + gate + persist
   (per device, instant)      (cheap, no LLM call)                    (LLM, only on miss/"fresh")
```

The library record is tagged (`grammar_points`, `theme`), and the **personalised
selector** (`select_from_library`) ranks unseen in-level stories by overlap with the
learner's weak skills — cheap, no LLM call, no change to generation. The forward-
compatible data model meant this dropped in without a refactor.

**Carrier reads are the personalised "fresh" path (ADR-021).** When the learner has
looked-up (unknown) words, the reader requests a *fresh* story seeded with those
words (`learning_words`) so they recur in context; with none pending, it serves from
the shared library. So personalisation rides the on-demand tier ADR-013 already
reserved, and every fresh story is still persisted for everyone.

## Tech choices

- **No frontend build step** — `index.html` is one self-contained file (design
  tokens + components + logic). A prototype should be trivially runnable.
- **stdlib server** — `http.server`, zero deps, reuses `eval/`. Production would
  swap to a real framework + DB, but the contracts stay.
- **Structured outputs everywhere** — the LLM returns schema-constrained JSON, so
  the harness and UI always get parseable, enum-constrained data (ADR-002).
- **Browser speech synthesis** for listening input — free, offline, no service.
- **Real NLP for the vocab gate** — `simplemma` (lemmatisation) + `wordfreq` (Zipf
  frequency) power `vocab_coverage.py`, so the lexical gate and the content-vocab
  axis are deterministic and data-driven, not hand-rolled heuristics (ADR-019).
- **Persistence today** is `localStorage` (client) + a JSON file (library). The
  data *shapes* are DB-ready; only the storage swaps.
