# Decision log (walkthrough)

Every significant decision, in the order it was made, with the context and the
reasoning — so a new architect or engineer can understand not just *what* the app
is but *why*. Format per entry: **Context · Decision · Why · Alternatives · Status**.

Cross-refs: [ARCHITECTURE.md](ARCHITECTURE.md), [PEDAGOGY_ROADMAP.md](PEDAGOGY_ROADMAP.md),
[CONTRIBUTING.md](../CONTRIBUTING.md).

---

### ADR-001 — Validate the feedback engine before building any UI
**Context:** The app's core risk is whether an LLM can reliably grade learner
German. **Decision:** Build an offline eval of the grammar-feedback engine first;
no UI until it passes. **Why:** Wrong feedback in a teaching app actively teaches
mistakes — it's worse than none. The risky thing must be proven in isolation.
**Alternatives:** Build UI first and "see how it feels" — rejected; it hides the
core risk. **Status:** Done; engine validated A1–C2.

### ADR-002 — Structured outputs (schema-constrained JSON) for all LLM calls
**Context:** Free-text model output is hard to score and render. **Decision:** Every
LLM call returns JSON constrained to a schema (`TutorFeedback`, story object).
**Why:** Guarantees parseable, enum-bounded results; the scorer and UI never see a
surprise. **Alternatives:** Parse prose with regex — brittle. **Status:** Done.

### ADR-003 — Headline metric = false-positive rate on *correct* sentences
**Context:** "Accuracy" alone hides the worst failure: inventing errors in good
German. **Decision:** Make ~half the eval cases already-correct, and treat the
false-positive rate as the make-or-break number. **Why:** A tutor that "corrects"
correct German destroys trust — the single biggest threat to the concept.
**Alternatives:** Optimise detection recall only — rejected. **Status:** Done;
0% false-positive on both models, A1–C2.

### ADR-004 — A closed error taxonomy as the single source of truth
**Context:** Categories are referenced by the dataset, the model's schema, the
scorer, and the UI. **Decision:** Define them once in `taxonomy.py`; everything
imports from there. **Why:** The model can only emit labels we score; no drift
between layers. **Alternatives:** Ad-hoc strings per layer — guarantees divergence.
**Status:** Done (20 categories).

### ADR-005 — LLM = Gemini on Vertex (via GCP ADC), isolated behind one file
**Context:** No Anthropic key in this environment, but Vertex (Gemini) credit is
available. **Decision:** Run on Gemini via GCP ADC, with *all* LLM access behind
`vertex_backend.py`. **Why:** Use available credit; keep the provider a one-file
concern so switching to Claude later is trivial. **Alternatives:** Block on getting
a Claude key — rejected; the harness is provider-agnostic by design. **Status:** Done.

### ADR-006 — Ship Gemini 2.5 Flash, not Pro
**Context:** Compared Pro vs Flash on the grammar eval. **Decision:** Use Flash.
**Why:** Flash matched or *beat* Pro (caught an irrealis error Pro missed at C2),
at ~2× speed and far lower cost. At per-answer scale, cost is decisive.
**Alternatives:** Pro for "max quality" — not justified by the data. **Status:** Done.

### ADR-007 — Expand the taxonomy to 20 categories for C1/C2
**Context:** The first 12 categories were basic/intermediate; C1/C2 grammar
(Konjunktiv I, Passiv, Nominalstil, participial attributes, modal particles) wasn't
representable. **Decision:** Add 8 advanced categories so the engine can *tag*
advanced grammar and the level→skill map is real. **Why:** Otherwise C1/C2 skill
bars are decorative — the engine could never move them. **Alternatives:** Leave
C1/C2 grammar coarse — rejected; would be dishonest. **Caveat:** The level→grammar
mapping is a standard-progression *heuristic*, not an official CEFR syllabus
(none is machine-readable). **Status:** Done.

### ADR-008 — FSRS spaced repetition for review
**Context:** Retention needs scheduled review, not re-reading. **Decision:** Use the
real FSRS forgetting curve `R(t,S)=(1+FACTOR·t/S)^DECAY` and retrieval-driven
scheduling; a *simplified* stability update (not the trained 19-weight model).
**Why:** FSRS is the modern state of the art; the curve + scheduling are the core
insight, the exact weights are an optimisation. **Alternatives:** SM-2 (older,
worse). **Status:** **Done — real FSRS-5.** The simplified update was replaced with
the actual FSRS-5 algorithm: official default parameters (`FSRS_W`) + the published
difficulty/stability equations. Implemented inline (no build step) but numerically
matches py-fsrs / ts-fsrs defaults (initial intervals 0.40/1.18/3.17/15.69 d;
mature growth 3→11→35→102→… d). Card shape (S, D, reps, last, due) unchanged.
**Next:** per-user parameter optimisation from review history.

### ADR-009 — Level is *measured*, not set; track grammar and vocabulary separately
**Context:** Should the user pick their level? **Decision:** No. Derive the current
level from performance (grammar mastery + words used), shown as two axes (e.g.
*Grammar A1 · Vocabulary A2*); the user sets only a **goal**. **Why:** Self-
assessment is unreliable; hand-setting breaks comprehensible input (too easy → no
i+1; too hard → not comprehensible). Proficiency isn't one number — CEFR explicitly
allows jagged profiles, and vocab-ahead-of-grammar is a common, real shape in German
learners. **Alternatives:** Manual level pills (the original prototype) — replaced.
**Caveat:** "Grammar level" isn't an official CEFR scale; present as a hedged
heuristic ("≈"). **Status:** Done.

### ADR-010 — Focused feedback: lead with one error, collapse the rest
**Context:** The engine returns *all* errors. **Decision:** UI surfaces the single
highest-priority (treatable, level-core) error; others collapse behind "+N more".
**Why:** Meta-analytic evidence (Ferris/Bitchener) — focused correction on treatable
errors beats comprehensive correction, which overloads and demotivates.
**Alternatives:** Show everything — rejected. **Status:** **Done, engine-side.** The
tutor returns `errors` already ordered by pedagogical priority (meaning-blocking and
treatable rule-based errors first); the UI just leads with `errors[0]` and dropped
its static client-side ranking. Ordering doesn't affect grammar scoring (the scorer
compares category *sets*).

### ADR-011 — Don't trust "write at level X"; gate generated stories with a judge
**Context:** The input half depends on stories staying in-level. **Decision:** A
story-in-level eval that *generates* with one model and *judges* with a **different**
one (avoids self-agreement), classifying three ways: above (drift) / on / below
(too easy). **Why:** arXiv 2505.08351 (2025) shows LLMs drift off a prompted CEFR
level — and our own longer-story sweep reproduced it (A2 stories leaked over-level
words). **Alternatives:** Trust the generation prompt — empirically wrong.
**Caveat:** The judge is itself an LLM, not ground truth — a drift *signal*, not a
certified grade. **Status:** Done.

### ADR-012 — i+1 gloss-whitelist: over-level words are OK *if glossed*
**Context:** A strict "no word above level" gate rejects pedagogically fine stories.
**Decision:** The gate accepts over-level words *if they appear in the story's
glossary* (i.e. they're supported). **Why:** That's exactly the "+1" of i+1 —
comprehensible input is meant to contain a few new, supported words. **Alternatives:**
Reject any over-level word — too strict, kills richness. **Status:** Done.

### ADR-013 — Story content: generate once, select per user, add as you go
**Context:** Should stories be generated on every read? **Decision:** No. Generate
into a **shared library** (tagged, gated), **select** per user cheaply, and grow the
library incrementally (background). Reserve on-demand for the long tail, folding
results back into the library. **Why:** A CEFR level is shared across users —
regenerating per read re-pays generation + gating cost forever, with latency every
time. The library converts a per-read variable cost into a one-time fixed cost
amortised across all users; it also enables extensive-reading *volume* and vocab
recycling, and moves the drift-gate to authoring time (where human QA can live).
**Alternatives:** On-demand-every-time — simple at tiny scale, doesn't scale.
**Status:** **Done.** Shared library with tagged, gated, persisted stories;
`select_from_library(level, weak_skills, exclude)` ranks unseen in-level stories by
overlap of `grammar_points` with the learner's weak skills (random among ties), no
LLM call. The reader sends `weak_skills` + `seen_ids`; carrier reads (ADR-021) still
take the fresh path. Remaining: theme/interest signal as a tiebreaker.

### ADR-014 — UI: content serif vs. chrome sans, calm semantics, one hero action
**Context:** The app puts a blank box in front of a beginner — UX must not add load.
**Decision:** Literary serif for German content, quiet sans for UI; one primary
action per screen; muted semantic colours (correction = green, attention = amber,
never alarm-red); an animated diff to make the error→fix gap *noticed*; browser TTS
for listening input; accessibility baseline. **Why:** Reduce extraneous cognitive
load (Sweller); engineer "noticing" (Schmidt); keep errorful learning safe, not
punishing; avoid the gamification overjustification trap. **Status:** Done.

### ADR-015 — Pedagogy grounded in cited, checkable research (incl. debated claims)
**Context:** Pedagogy claims must be verifiable, not vibes. **Decision:** A roadmap
mapping every feature to a research principle, with DOIs/links and explicit
**[debated]** flags (Krashen i+1, Bloom 2σ, the Truscott–Ferris debate). **Why:**
Checking sources should reveal nuance; build on the solid parts. **Status:** Done
([PEDAGOGY_ROADMAP.md](PEDAGOGY_ROADMAP.md)).

### ADR-016 — Offline rigour (Pro) vs. in-app guard (Flash); never spend in the request path
**Context:** Judging/gating costs calls. **Decision:** Offline evals use Pro and full
datasets for confidence; the in-app gate uses Flash and the library serves most
reads. **Why:** Pay for rigour where it compounds (offline), stay cheap where it
scales (per request). **Status:** Done.

### ADR-017 — Reuse the eval code at runtime (no test/prod split)
**Context:** Risk that "what we tested" diverges from "what ships". **Decision:** The
server imports the same `eval/` modules (`tutor`, `vertex_backend`, `story_service`).
**Why:** The validated engine *is* the production engine. **Alternatives:** A separate
prod implementation — invites drift between measured and shipped behaviour.
**Status:** Done.

### ADR-018 — Grammar is the target; the cloze blank is always a grammatical function
**Context:** Should review train word meaning? **Decision:** No. Every training item
is a cloze whose gap tests a *grammatical* form (case, ending, verb position, aux,
preposition…), tagged by taxonomy category; the cue supplies meaning (base form),
grading is exact-match, and it feeds the grammar profile. **Why:** the moat is
German grammatical accuracy; vocab recall is a different, crowded product.
**Supersedes:** the vocabulary half of ADR-008 (FSRS schedules *grammar* items now).
**Status:** **Done.** The review deck is grammar-only typed cloze; vocab cards
removed; `mintErrorCards` turns each corrected mistake into a cloze from the
learner's own sentence; exact-match grading feeds `profile.skills[category]`.
See [PEDAGOGY_ROADMAP.md → Content design #1](PEDAGOGY_ROADMAP.md).

### ADR-019 — Vocabulary is capped per level (controlled vocabulary)
**Context:** Comprehensible input needs the learner to already know most words.
**Decision:** Content draws from a per-level allowed lexicon (frequency bands /
Goethe lists) + a small glossed i+1 budget; the story gate adds a **measurable
lexical-coverage check** (in-band lemma fraction), not just the LLM judge. **Why:**
~95–98% known-word coverage is required for comprehension (Hu & Nation 2000); the
cap *is* the i+1 mechanism, and coverage is measurable where the judge is not.
**Status:** **Done, on real data.** `vocab_coverage.py` lemmatises with `simplemma`
(handles irregulars: fuhr→fahren) and bands by `wordfreq` Zipf frequency (lexical
frequency profiling, Laufer & Nation 1995) — replacing the earlier bootstrap-band +
heuristic-stemmer approach (both deleted). Story gate requires `judge_ok AND
coverage≥0.85`, reporting `coverage`/`uncovered_words` in `check`; the same module
powers the content-vocabulary axis (`classify_vocab`, ADR-009). **Caveat:** Zipf
frequency is a principled but imperfect CEFR proxy (some basic-but-rare words
mis-rate), so the threshold stays lenient and the gate's job is *gross* drift; the
LLM judge handles nuance. Tunable: `ZIPF_BANDS` thresholds.

### ADR-020 — Meaning is a subtle comprehension aid, never trained or featured
**Context:** How prominent should word meaning be? **Decision:** A lookup is an
ephemeral, quiet gloss — no flashcard, no XP, no "added to deck." It exists only to
make the current sentence comprehensible. **Why:** incidental acquisition via input
(Krashen; Webb), not deliberate study; meaning is plumbing, not a feature.
**Status:** **Done.** The gloss sheet is view-only (Hear-it remains); the
"add to review" affordance and all gloss→deck enrolment are removed. A lookup only
increments an ephemeral `encounters` counter (the ADR-021 signal).

### ADR-021 — Vocabulary acquired incidentally via grammar-cloze carrier frequency
**Context:** If we don't test vocab, how is it learned? **Decision:** A gloss-tap is
an "unknown word" signal; unknown words are preferentially reused as the **carrier
words** in upcoming grammar cloze items (more meaningful exposure). Unknown-status
decays as the learner stops looking the word up. **Why:** ~8–12 meaningful
encounters drive uptake (Nation; Webb); this routes them through the grammar loop
and uses the lookup as a free implicit mastery signal. **Caveat:** the
no-lookup→known signal is noisy — soft prior over several encounters, not a verdict.
**Status:** **Done.** Lookups increment `profile.encounters`; the reader sends the
top unknown words as `learning_words`, and the generator weaves them into a *fresh*
story (so they recur in the reading + its questions). Decay: a carrier seen but not
looked up increments `seenNoLookup`; after 2, the word is marked `known` and loses
its boost. Invisible to the user — meaning is never shown as a feature.

### ADR-022 — Native-authentic German *within* the cap; naturalness as a 2nd judge axis
**Context:** Capping vocabulary risks stilted "Lehrbuchdeutsch". **Decision:** Treat
*range* (capped) and *naturalness* (always native) as independent axes — simple
words, real language: real collocations, modal particles, natural order,
contractions; functional/professional register at B2–C2. The story judge scores a
separate **naturalness** axis (native vs. textbook/translationese). **Why:**
native-like fluency is formulaic/collocational (Wray); authentic input beats
contrived (Gilmore); the two axes don't trade off. **Status:** **Done.** The
generator prompt demands native register (collocations, modal particles,
contractions); the judge scores a separate `naturalness` 1-5 axis + flags
`unnatural_phrases`; the gate ships only `naturalness≥4` and re-styles on a miss.
The eval reports per-story naturalness + an average.

### ADR-023 — Analytics logging is opt-in, pseudonymous, no-PII, with rights (GDPR/BDSG)
**Context:** We want learning data (to optimise FSRS, calibrate the judge/level, and
improve feedback), but the app runs under EU/German law. **Decision:** Log **nothing
until explicit opt-in consent** (Art. 6(1)(a) + TDDDG §25); store **no** name/email/
account/IP/fingerprint; group events by a **random pseudonymous id**; coarsen
timestamps to the day; expose **export** (Art. 15/20) and **delete** (Art. 17) +
consent withdrawal in-app; never commit event data (git-ignored). **Why:** data
minimisation + consent is the lawful, low-risk path; truly anonymous-ish learning
events still let us optimise without identifying anyone. **Also documented:** the
*service* itself sends learner text to the LLM provider (a processor) — a separate
Art. 6(1)(b) flow needing a DPA + transfer assessment in production. **Status:**
**Done (prototype).** See [PRIVACY.md](PRIVACY.md); production checklist there is
not yet implemented. Not legal advice — needs DPO/lawyer review before launch.

---

## Open decisions / next up
These are **calibration / data** tasks (not feature code). `analyze_events.py`
already reports the readiness/calibration stats for them from consented event logs:
- Per-user **FSRS parameter optimisation** from review history (ADR-008) — the
  analysis exports an optimiser-ready review log + a predicted-vs-actual recall check.
- **Calibrate the story judge** against human CEFR ratings (ADR-011); tune `ZIPF_BANDS`
  (ADR-019) — the analysis reports per-level coverage/naturalness/on-band in the wild.
- Theme/interest signal as a selector tiebreaker (ADR-013).
- Validate the **level→grammar map** against a real syllabus (ADR-007).
