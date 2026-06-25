# Fix plan — restoring the "measured, not declared" promise

A deep, tracked plan to fix the pedagogical and UI issues found in a review of
the prototype (see the critique in the project history). The engine (feedback,
gating) is sound; the gaps are in the **measurement and retention layers**, which
are currently gameable, self-reported, or disconnected from real errors.

> **Status legend:** ☐ todo · ◐ in progress · ☑ done. Update the checklist and the
> **Status log** at the bottom every time an item lands.

## Guiding constraints (from CONTRIBUTING.md)
- **Additive contract changes only** — `TutorFeedback`, the story object, and the
  profile get new fields, never renamed/repurposed.
- **No grammar/level logic in the UI** — linguistic judgment is server-side; the
  browser renders.
- **One source of truth** — reuse `taxonomy.py`, `vocab_coverage.py`; don't fork lists.
- **Validate risky model-output changes with an eval first** (principle #5).
- **Provider boundary** — prompt/schema changes touch `tutor.py` only; `vertex_backend.py`
  just propagates the schema.

---

## Phase 0 — Foundations & honest cold start  ✅ done
- ☑ **MIG** Profile/deck schema version (`profile.v=2`) + `migrate()` from the v1
  `plappo2` key, so later metric changes can't corrupt existing `localStorage`.
  Fresh deck starts empty; demo deck only via `?demo=1`.
- ☑ **U1** Zero-start: `freshProfile()` → `level A1, xp:0, streak:0`, empty skills
  (no fabricated "🔥 5 / 240 XP"). `?demo=1` loads `demoProfile()`, labeled demo.
  Static header defaults neutralised (🔥 0, hidden due-badge).
- ☑ **U1b** First-run cue in `renderLearn` ("New here? Let's measure your level")
  replaces fabricated weak-skill recommendations until the first answer; the first
  checked answer sets `onboarded=true`. (Full blocking placement = still optional.)

## Phase 1 — Measurement validity (the core claim)
- ☑ **P1-eval** `eval/skills_demonstrated_eval.py` measures contradiction rate
  (demonstrated ∩ errors → must be 0), advanced over-claim on A1/A2 correct
  sentences (→ ~0), and coverage. `--mock` mode verified it catches an injected
  over-claim. **Run live with creds before fully trusting the field.**
- ☑ **P1** `TutorFeedback.demonstrated: List[ErrorCategory]` added (additive);
  `SYSTEM_PROMPT` updated + stale "A1-B2"→"A1-C2"; mirrored in `vertex_backend.py`
  `_RESPONSE_SCHEMA` (not required); `applyResult` now credits only exercised
  skills (`-` errored, `+` demonstrated) — blanket +6 removed. Empty `demonstrated`
  → no positive movement (safe default, robust if the model omits the field).
- ☑ **P2** Vocabulary by content lemmas vs bands, decoupled from correctness:
  `classify_vocab()` added to `vocab_coverage.py` (reuses stemmer/function-words/
  bands, tags each lemma with its lowest band); `/api/feedback` returns
  `content_lemmas`; client tracks `seenLemmas` and counts distinct content lemmas
  regardless of errors (migrated counts preserved via `max`). Unit-tested.
- ☑ **U3** Contingent praise: verdict now names a real strength from `demonstrated`
  ("Your Verb position was right — one thing to fix"), falling back to neutral. RNG
  `PRAISE[]` removed.
- ☑ **U4** Single precision register: per-skill scores render as bands
  (Mastered/Building/Started/New) via `skillBand()`, not raw integers; bar width
  still reflects the underlying value. Vocab keeps a genuine count.

## Phase 2 — Close the feedback → retention loop
- ☑ **P6** `mintErrorCards(fb)` (called from `applyResult`): each corrected error
  becomes a grammar cloze from the learner's own corrected sentence (blank the
  fixed span), tagged category + explanation, due in ~6h, deduped by
  category+cloze. Closes the feedback→retention loop.
- ☑ **P5** `openDrill(cat, sentence, why)` rebuilds the learner's own corrected
  sentence as the tap-to-build target; "Drill this" passes it via `lastDrill`/
  `drillFromFeedback()` (avoids quoting a sentence into inline onclick). Canned
  `DRILLS` remain the fallback for weak-skill drills opened from the Learn tab.
- ☑ **P4** Verified type-to-recall: review cards now take a typed answer, checked
  via `normAns`/`acceptsFor` (case/punctuation/umlaut-transliteration tolerant,
  article-optional for vocab, optional `it.accept[]`). FSRS grade is derived from
  the verified result (correct+fast → Easy, correct → Good, wrong/gave-up → Again)
  and highlighted, with manual override retained. "Show answer" still available.
- ☑ **P3** Gloss lookup no longer auto-enrolls; the sheet has an explicit
  "+ Add to review" button (`addCurrentVocab`). Encounters are tracked
  (`profile.encounters`) and after a 2nd encounter the button nudges
  ("seen N×") — but never adds without a tap. Button reflects "✓ In your reviews".

## Phase 3 — Content depth, accessibility, polish, QA
- ☐ **P7** Task-based prompts in story generation (additive on story `questions`);
  small generation eval. *(largest item — may split/defer)*
- ☑ **U2** Real reading progress: dots now light by scroll position
  (`paintProgress`), all lit if the story fits without scrolling; no fake default.
- ☑ **U5** A11y + autoplay: glossed words are keyboard-reachable buttons
  (role/tabindex/Enter-Space/aria-label); diff `del`/`ins` carry was/corrected
  labels (not color-only); auto-`speak()` removed on correct-answer and reveal —
  TTS now only via the explicit 🔊 / "Hear it" buttons.
- ☑ **U6** Offline rotation: real stories cached per level (last 5); offline
  serves a random saved story, falling back to the hardcoded one only if none.
- ☑ **U7** Documented the 412px phone-frame mock + `?demo=1` in `prototype/README`
  (chose to document rather than rework into a responsive layout).
- ☐ **U8** Manual QA checklist over every open/close/first-run/offline/error path.

---

## Data-contract changes (all additive)
| Shape | New fields | Where |
|---|---|---|
| `TutorFeedback` | `demonstrated: [ErrorCategory]` | `tutor.py` (+ mirror in `vertex_backend.py`) |
| `/api/feedback` response | `content_lemmas: [str]` | `server.py` + `vocab_coverage.classify_vocab` |
| story object | optional task framing on `questions` | `story_service.py` |
| profile | `v`, `onboarded`, `seenLemmas`, `encounters` | `prototype/index.html` |
| review item | `accept[]`, error-sourced cloze fields | `prototype/index.html` |

## Commit sequence
0 → P2 → (P1-eval → P1 → U3/U4) → (P6 → P5 → P4 → P3) → Phase 3 (P7 last).

---

## Status log
- **Phase 0 done** — honest cold start + profile/deck v2 migration. New users start
  at A1 with zero history and a calibration cue; demo data behind `?demo=1`.
- **P2 done** — vocabulary measured from content lemmas (server `classify_vocab`),
  function words excluded, decoupled from grammar correctness. `/api/feedback`
  now returns `content_lemmas`. (Live end-to-end needs `VERTEX_PROJECT`; the
  classifier itself is unit-tested.)
- **P1 done** — the keystone. Skills now move only when actually exercised
  (`demonstrated`), not on a blanket "no error" bonus. New eval gates the field's
  trustworthiness; `--mock` verified mechanics + back-compat (`run_eval --mock`
  still passes). ⚠️ Run `skills_demonstrated_eval.py` live (Vertex) before relying
  on the field — until then the UI degrades safely (no credit when unsure).
- **U3/U4 done** — Phase 1 complete. Praise is now earned (names a real
  `demonstrated` strength); skill bars show qualitative bands, not pseudo-precise
  integers. Both ride on P1's `demonstrated` signal.
