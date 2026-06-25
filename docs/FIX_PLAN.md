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
- ☐ **P1-eval** `eval/skills_demonstrated_eval.py` (or extend `dataset.py`): measure
  precision of the new `demonstrated` field; no false "demonstrated" on dodged
  constructions. Gate the UI change on this.
- ☐ **P1** Extend `TutorFeedback` with `demonstrated: List[ErrorCategory]`; update
  `SYSTEM_PROMPT` (and fix stale "A1-B2" → "A1-C2"); mirror schema in
  `vertex_backend.py`; rewrite `applyResult` to credit only exercised skills
  (`-` errored, `+` demonstrated), no blanket +6.
- ☑ **P2** Vocabulary by content lemmas vs bands, decoupled from correctness:
  `classify_vocab()` added to `vocab_coverage.py` (reuses stemmer/function-words/
  bands, tags each lemma with its lowest band); `/api/feedback` returns
  `content_lemmas`; client tracks `seenLemmas` and counts distinct content lemmas
  regardless of errors (migrated counts preserved via `max`). Unit-tested.
- ☐ **U3** Contingent praise from real `demonstrated` strengths; drop the RNG.
- ☐ **U4** One precision register — banded skill labels/bars, hide raw integers.

## Phase 2 — Close the feedback → retention loop
- ☐ **P6** On each error, mint a grammar cloze review card from `corrected_sentence`
  (blank the corrected fragment), tagged category + explanation; dedup.
- ☐ **P5** `openDrill(cat, correctedSentence, fragment)` builds tap-to-build from the
  learner's corrected sentence; `DRILLS` only as fallback.
- ☐ **P4** Verified type-to-recall on review cards; derive FSRS grade from
  correctness (+latency); manual override kept. Items gain `accept[]`.
- ☐ **P3** Remove auto-enroll on gloss open; explicit "+ Add to review" button;
  optional auto-suggest after 2nd encounter (`encounters[lemma]`).

## Phase 3 — Content depth, accessibility, polish, QA
- ☐ **P7** Task-based prompts in story generation (additive on story `questions`);
  small generation eval. *(largest item — may split/defer)*
- ☐ **U2** Real reading progress (IntersectionObserver); remove fake "first-two-lit".
- ☐ **U5** A11y: tappable words as real buttons (role/tabindex/keys/aria); don't rely
  on color alone; stop autoplaying TTS, add mute.
- ☐ **U6** Offline fallback rotation (cache last N stories per level).
- ☐ **U7** Responsive desktop reading layout, or document the 412px phone mock.
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
