# Plappo

Learn German by **reading short stories at your level, writing your own answers,
and getting focused grammar feedback** — on a spaced-repetition schedule, adapting
to a level the app **measures** rather than asks you to declare.

It's an AI writing tutor for German: the differentiator isn't the stories, it's
**reliable feedback on free-written production** (where most apps only offer
tap-the-tiles). The whole project is built feedback-engine-first, validated by
offline evals before any UI.

## The user story

> Lena is roughly A2. She opens Plappo — no level to pick; the app already knows
> her **grammar is around A1 but her vocabulary is A2** from how she's been doing.
> It gives her a short story at her level (verified in-band before she sees it).
> She taps `Sandburg` to see "sandcastle" — and it quietly enters her review deck.
> She answers a question in German: *"Weil sie hat den Schlüssel verloren."* The
> app shows the one thing to fix — `weil` sends the verb to the end — corrects it,
> and her **grammar profile nudges up**. Tomorrow her review surfaces `Sandburg`
> right as she'd start to forget it, and her next story is a notch harder.

## What works today (all live, on Gemini via Vertex)

- **Grammar feedback engine** — structured, validated **A1–C2**, **0% false-positive
  rate** on correct sentences (the trust metric).
- **Measured level** — grammar and vocabulary tracked as separate axes; level is
  earned, not set; you choose only a goal.
- **FSRS spaced repetition** — real forgetting curve; glossed words auto-enter review.
- **Focused live feedback** — leads with the single most important error.
- **Level-gated story generation** — stories are generated *and judged in-band*
  before they ship, and persisted to a growing shared library.

## Quickstart

Prereq: `gcloud auth application-default login` (Gemini-on-Vertex via ADC).

```bash
# 1) Run the app
cd prototype && python server.py          # → http://127.0.0.1:8000

# 2) Run the offline evals (the "is it good?" proof)
cd eval && pip install anthropic pydantic
python run_compare.py                      # grammar feedback: Pro vs Flash, A1–C2
python story_level_eval.py --levels A2,B1,B2 --sentences 12   # story-in-level drift
```

## Documentation map

| Doc | What it covers |
|---|---|
| [CLAUDE.md](CLAUDE.md) | **Engineering standards** — how to write code here without future refactors |
| [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) | Components, data flow, **data contracts**, runtime vs offline, scaling |
| [docs/DECISIONS.md](docs/DECISIONS.md) | **Decision walkthrough** (ADRs) — every choice and its reasoning |
| [docs/PEDAGOGY_ROADMAP.md](docs/PEDAGOGY_ROADMAP.md) | The learning science, phased roadmap, **cited & checkable** sources |
| [eval/README.md](eval/README.md) | The eval harnesses + latest results |
| [prototype/README.md](prototype/README.md) | The app prototype: screens, what's real vs stubbed |

## Project layout

```
eval/        offline measurement + the LLM service layer (the source of truth)
prototype/   the runnable app (stdlib server + single-file UI), reuses eval/
docs/        architecture, decisions, pedagogy
```

## Honest status

This is a validated **prototype**, not production. The risky cores — reliable
feedback and in-level content — are proven by evals and running live. Known limits
are documented per-decision in [docs/DECISIONS.md](docs/DECISIONS.md): the LLM judge
isn't ground truth, the level→grammar map is a heuristic, FSRS is a faithful
simplification, and persistence is `localStorage` + a JSON file (DB-ready shapes).
The next steps are listed there too.
