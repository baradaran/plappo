# German grammar-feedback eval harness

The point of this harness is to answer **one question before any UI gets built**:
*can an LLM reliably give correct, level-appropriate German grammar feedback?*
If it can't, the whole app idea doesn't work — so we test the engine in isolation.

## What it measures

For each learner sentence (some with known errors, ~half already correct):

1. **Error detection** — does it spot a problem at all? Recall on error sentences,
   and the **false-positive rate on correct sentences** — the trust metric. A
   teaching app that invents errors in good German actively teaches mistakes.
2. **Category** — is the *kind* of error right? Micro precision/recall/F1 over a
   closed [taxonomy](taxonomy.py).
3. **Correction** — does its rewrite match the canonical fix? (Strict,
   punctuation-insensitive, case-sensitive.)
4. **By level** — does it fall apart at B1/B2 vs A1?

## Run it

```bash
pip install anthropic pydantic

# Verify the harness works with no API key (deterministic mock tutor):
python run_eval.py --mock
```

### Against Gemini on Vertex (current setup)

There's no Anthropic key in this environment, so the live runs use **Vertex
AI (Gemini)**. Auth is GCP ADC (`gcloud auth application-default login`);
project/location are read from a local `.env` (`VERTEX_PROJECT`,
`VERTEX_LOCATION`) or process env (override the path with `VERTEX_ENV`). See
`vertex_backend.py`.

```bash
# Pro vs Flash, side-by-side, over the whole dataset:
python run_compare.py

# Or pick models explicitly:
python run_compare.py gemini-2.5-flash gemini-2.5-pro
```

> This evaluates **Gemini**, not Claude — a deliberate, user-directed choice
> because that's where the credit is. The harness is provider-agnostic; the
> tutor is just a function returning structured feedback.

### Against Claude (if you get an Anthropic key)

```bash
export ANTHROPIC_API_KEY=sk-ant-...     # PowerShell: $env:ANTHROPIC_API_KEY="..."
python run_eval.py
GERMAN_TUTOR_MODEL=claude-sonnet-4-6 python run_eval.py
```

Each run writes `results/<model>_<timestamp>.json` with per-case predictions, so
you can eyeball *what* it got wrong, not just the score.

## Files

| File | Role |
|------|------|
| `taxonomy.py` | The closed set of error categories (shared by all three layers). |
| `dataset.py` | Gold cases: learner sentence → canonical fix + error categories. |
| `tutor.py` | The engine under test — Claude with a structured-output schema. |
| `score.py` | Detection / category / correction metrics. |
| `run_eval.py` | Runner + report. |
| `vertex_backend.py` | Gemini-on-Vertex engine (GCP ADC auth). |
| `run_compare.py` | Run several Vertex models and print a side-by-side. |
| `mock_tutor.py` | Deterministic fake for `--mock`. |

## Latest result (Gemini 2.5 Pro vs Flash, 26 cases)

| metric | Pro | Flash |
|---|---|---|
| Detection recall | 100% | 100% |
| **False-positive rate on correct sentences** | **0%** | **0%** |
| Correction accuracy (error sentences) | 100% | 100% |
| Category F1 | 0.90 | 0.90 |
| avg latency / call | 6.2s | 3.2s |

Both models pass the trust metric cleanly and produce correct rewrites on every
case. The 0.90 category F1 comes from two *labeling* mismatches, not grammar
errors: `warten auf dem Bus` (CASE vs PREPOSITION — these overlap in our own
taxonomy) and the double-error `Mit ein guter Freund` (model tagged one category
but fixed both). **Caveat:** 26 hand-written cases is enough to prove the
pipeline and that the model is strong, *not* to trust 100% — the next step is a
bigger, harder dataset to find where it breaks.

### Advanced end (C1/C2, 12 cases) — `run_compare.py --levels=C1,C2`

| metric | Pro | Flash |
|---|---|---|
| Detection recall | 83% (5/6) | **100% (6/6)** |
| **False-positive rate on correct** | **0%** | **0%** |
| Correction accuracy | 83% | **100%** |
| Category F1 | 0.73 | 0.67 |

The trust metric still holds (0% false positives on correct Konjunktiv I, modal
particles, gerundive attributes). Flash *beat* Pro — caught `würde…gekommen sein`
→ `wäre…gekommen` (irrealis) that Pro missed. Category F1 drops because advanced
topics overlap (`je…desto` is both CONNECTOR and WORD_ORDER) — detection +
correction are the metrics that matter here. `SUBJUNCTIVE_I` / `NOMINALIZATION` /
`MODAL_PARTICLE` are tested only via correct-sentence (false-positive) cases,
because as *errors* they're register/style, not hard rules. 12 cases is
directional, not conclusive — but hard enough to separate the models.

## Story-in-level eval (the INPUT side)

The grammar eval above tests *feedback on the learner's output*. This separate
eval tests *generated input*: does a German story actually land ON its target
CEFR level? Generate with one model, judge with a **different** one (avoids a
model grading itself kindly). Three-way: ABOVE (drift), ON (ship), BELOW (too easy).

```bash
python story_level_eval.py                          # A1/A2/B1, 5 sentences
python story_level_eval.py --levels A2,B1,B2 --sentences 12
```

Finding: short stories stay in band, but **longer A2 stories drift up** (leak
over-level words like `Schulgebäude`, `umarmt`) — confirming arXiv 2505.08351
(2025) that "write at level X" is not reliable. So the app gates generation on
**three axes**: the LLM judge's CEFR level (over-level words OK **iff glossed** —
that's i+1, ADR-012), a deterministic **lexical-coverage** check (`vocab_coverage.py`
via `simplemma`+`wordfreq`, ADR-019), and a **naturalness** score 1-5 (native vs.
textbook, ADR-022). `story_service.py` ships only stories that pass all three and
re-generates on a miss; wired into the reader via the server's `/api/story`. The
eval prints coverage and naturalness per story.

## Analysing the event log (`analyze_events.py`)

Once learners opt in (GDPR consent — see [docs/PRIVACY.md](../docs/PRIVACY.md)),
the app writes no-PII events to `prototype/data/events.jsonl`. This offline tool
turns them into what we collected them for — no network, no LLM:

```bash
python analyze_events.py                 # report
python analyze_events.py --write-log     # also export an FSRS optimiser review log (CSV)
```

- **FSRS** — review counts, grade distribution, and a **calibration** check
  (predicted recall from stability+elapsed vs. actual success, binned) that tells
  you whether the scheduler's parameters need re-optimising. `--write-log` exports
  a `(user, card, date, elapsed_days, rating)` CSV an FSRS optimiser can train on.
- **Content gate** — per-level on-band rate, avg coverage + naturalness, avg
  generation attempts, library-vs-generated split (judge/gate calibration in the wild).
- **Feedback** — first-try-correct rate, most common errors, most demonstrated skills.

## How to read the result

The number that decides viability is the **false-positive rate on correct
sentences**. Targets to aim for before building further:

- false-positive rate on correct sentences: **< 5%**
- detection recall on error sentences: **> 90%**
- category F1: **> 0.8**

If real-API numbers are far from these, the answer is *not* "ship anyway with a
disclaimer" — it's to improve the engine (better prompt, few-shot examples,
a verification pass) until they hold, or rethink free-text feedback.

## Extending the dataset

Add `Case(...)` rows in `dataset.py`. Real learner sentences (e.g. from a German
learner error corpus, or your own beta testers) make this far more predictive
than hand-written ones — grow it to 100+ cases per level before trusting the
numbers. Keep ~half the cases already-correct.
