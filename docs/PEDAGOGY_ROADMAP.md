# Plappo — Pedagogy Roadmap

**The bet:** most language apps optimise for engagement (streaks, taps, recognition).
Plappo optimises for the thing that actually builds a second language — *meaningful
input, real production, and focused feedback on a forgetting-proof schedule.* This
document maps every feature to the learning-science principle it serves, so we never
build a mechanic that looks fun but teaches nothing.

> Format: **what we build** on the left, **why (the research)** on the side. Status:
> ✅ done & validated · 🔜 next · 🧭 later · ⚠️ open risk.

---

## The six principles everything ladders up to

| # | Principle | Grounded in |
|---|-----------|-------------|
| **P1** | Meaningful **input** comes before output — slightly above current level (*i+1*), grammar met *in context*, not as isolated rules. | Krashen (Comprehensible Input); Long (Focus on **Form**, not Forms) |
| **P2** | **Production** is where acquisition happens — producing language forces deeper processing than recognising it. | Swain (Output Hypothesis); Schmidt (Noticing); the Generation Effect |
| **P3** | **Feedback** must be *focused, timely, actionable* — a few treatable errors, not every mistake. | Ferris & Bitchener (focused written corrective feedback); Hattie (feed-up / feed-back / feed-forward) |
| **P4** | You remember by **retrieving on a schedule** — spaced, interleaved, effortful recall. | Bjork (desirable difficulties); Roediger (testing effect); FSRS |
| **P5** | **Motivation** is intrinsic or it's fragile — competence, autonomy, relatedness beat points. | Deci & Ryan (Self-Determination Theory); Bloom (Mastery Learning); Csíkszentmihályi (Flow) |
| **P6** | **Adapt to the individual** — 1:1 tutoring is the gold standard; an error profile makes it scalable. | Bloom (2-sigma); Vygotsky (ZPD / dynamic assessment); learner-corpus research |

---

## Phase 0 — Foundations *(✅ done & validated)*

| What we built | Why — the side note |
|---|---|
| **Reliable grammar-feedback engine** (structured: error spans, category, correction, explanation) — validated A1→C2, **0% false-positive rate** on correct sentences. | **P3.** A teaching tool that invents errors in good German actively *teaches* mistakes and destroys trust. "Don't be wrong" had to be proven *before* any UI — it was. |
| **Free-text answers**, not multiple choice. | **P2 (Generation Effect).** Producing a sentence builds far stronger memory than tapping tiles. This is the core differentiator, and it only works because the engine is trustworthy. |
| **CEFR-accurate level model A1–C2** with grammar mapped to the Goethe progression. | **P1 / P5 (Flow).** Challenge must match skill. Levels are the scaffold that keeps input in the *i+1* band. |
| **Learner profile** — per-skill mastery + % to next level. | **P5 (Competence) / P6.** Visible competence is the strongest intrinsic motivator; the profile is also the data substrate for personalisation. |

---

## Phase 1 — Make the core loop *pedagogically* correct *(🔜 next)*

| What we build | Why — the side note |
|---|---|
| **Focused feedback ranking** — surface the **1–2 highest-priority errors** per answer (by level + current focus skill), not all of them. | **P3 ⚠️.** *The* key research nuance. Truscott argued correction is useless; Ferris/Bitchener showed it works **only when focused** on *treatable, rule-based* errors (German case, gender, agreement, verb position — a perfect fit). Comprehensive correction overloads and demotivates. Engine change: rank, then withhold the minor ones. |
| **FSRS scheduling** for vocabulary *and* grammar points (replaces the naive ±strength decay). | **P4.** FSRS is the current state of the art in spaced repetition — it predicts *when* you're about to forget and reviews just in time. Single highest-leverage upgrade to retention. |
| **Noticing-optimised feedback card** — make the gap between *your form* and the *correct form* visually unmissable; one-line, act-on-it explanation. | **P2 (Noticing) / P3 (Hattie).** Learning happens at the moment you *notice* the difference. The card's job is to engineer that noticing, then tell you exactly what to do next. |
| **i+1 story calibration** — generated/curated stories that are mostly known vocab + a few inferable new words. | **P1.** Input that's too hard isn't comprehensible; too easy isn't acquisition. The whole input engine lives or dies on staying in the *i+1* band — and this is still **unvalidated** (see risks). |

---

## Phase 2 — Adapt and schedule *(🧭 later)*

| What we build | Why — the side note |
|---|---|
| **Profile-driven content selection** — the error profile chooses your *next* story and drills (weak skills resurface in context). | **P6 (2-sigma) / P3 (feed-forward).** This closes the loop from *"we detected your weakness"* to *"so here's the input that targets it."* It's what makes an app behave like a 1:1 tutor. |
| **Interleaved + spaced drills** — mix error categories rather than blocking one type; schedule via FSRS. | **P4 (Bjork).** Interleaving and spacing feel harder and *are* harder — that's the point ("desirable difficulties"); they produce durable, transferable skill where blocked practice produces fragile recall. |
| **Extensive reading library** — volume of graded, level-appropriate stories, not one-offs. | **P1.** Acquisition scales with *volume* of comprehensible input (the graded-reader / Dreaming-Spanish insight). One story a day isn't enough input to move a level. |
| **CEFR Companion-Volume can-do descriptors** — "At B1 you can…" framing tied to official 2020 descriptors. | **P5 (Competence) / P6.** Concrete can-do goals (not just %) give meaning to progress and a shared, standards-based definition of "ready to level up." |

---

## Phase 3 — Deepen production & motivation *(🧭 later)*

| What we build | Why — the side note |
|---|---|
| **Task-based prompts** — answers that accomplish a real communicative goal (write the reply, summarise, persuade), not just "answer the question." | **P2 (TBLT).** Task-Based Language Teaching: language sticks when it's a *means to an outcome*, not the object of study. Richer output → more to give feedback on. |
| **Metacognition / reflection** — the weak-spots panel becomes reflective ("here's your pattern, here's why, here's the plan"). | **P5 / learning-to-learn.** Learners who understand *how* they're progressing self-regulate better and persist longer. |
| **Relatedness features** — shared stories, peer answers, light community. | **P5 (SDT) ⚠️.** Competence and autonomy are covered; **relatedness is the missing leg** of intrinsic motivation and the biggest untapped retention lever. |
| **Restraint on gamification** — streaks/XP as *light* scaffolding, never the core loop. | **P5 ⚠️.** The overjustification effect: pile on extrinsic rewards and you can *erode* the intrinsic motivation that actually sustains learning. Resist the Duolingo-confetti reflex. |

---

## Phase 4 — New modalities & deeper assessment *(🧭 later)*

| What we build | Why — the side note |
|---|---|
| **Listening input** (audio stories) and eventually **speaking** production. | **P1 / P2.** Reading is one input channel; real proficiency is multi-modal. Listening is comprehensible input too; speaking is pushed output. |
| **Dynamic assessment** — assessment fused with instruction (graduated hints before the full correction). | **P6 (Vygotsky / ZPD).** Don't just mark right/wrong — find the edge of what the learner can do *with support*, and teach exactly there. |
| **Learner-corpus analytics** — aggregate anonymised errors to improve the taxonomy, drills, and i+1 calibration over time. | **P6.** The product gets smarter as more learners use it: real error data > our hand-written guesses (the caveat that's run through every eval). |

---

## Cross-cutting open risks ⚠️

| Risk | Why it matters | Status |
|---|---|---|
| **Story generation that stays inside a CEFR level** | The *input* half of the app. An LLM that leaks B2 vocab into an A2 story breaks *i+1* (P1). **Empirically confirmed risk:** LLMs measurably drift off a prompted CEFR level (arXiv [2505.08351](https://arxiv.org/abs/2505.08351), 2025). | Needs its own eval (a "does this A2 story stay A2?" checker) before we build on it — do **not** trust the prompt alone. |
| **Corrective-feedback dosage** | Over-correct and you violate P3 and demotivate; under-correct and learning stalls. | Tunable via the focused-feedback ranking (Phase 1). |
| **Advanced-level grammar is partly *style*, not rules** | At C1/C2, much "grammar" is register/preference; the engine rightly stays silent. Don't fake error cases there. | Surfaced in the C1/C2 eval; handled by testing those skills via correct-sentence (false-positive) cases. |
| **CEFR has no canonical machine-readable grammar syllabus** | Our level→skill mapping is *standard*, not authoritative. | Validate against a real syllabus (Goethe inventories) before high-stakes claims. |

---

## How we'll know the pedagogy is working (not just the engagement)

| Signal | Principle it proves |
|---|---|
| Engine false-positive rate stays ~0% as content scales | P3 (trust) |
| Errors in a skill *decline* over spaced repetitions (not just first-try accuracy) | P4 (durable retention) |
| Time-to-level-up correlates with real CEFR can-do performance | P1 / P5 (valid progression) |
| Retention/return-rate driven by competence + relatedness, not streak pressure | P5 (intrinsic motivation) |
| Profile-selected content reduces repeat errors faster than random content | P6 (personalisation works) |

---

## Resources & how to check them

Each principle below lists its key source(s) so any claim in this roadmap is
traceable. **Verify exact bibliographic details (volume/page/DOI) before quoting in
anything public** — these are accurate to author/year/title/venue from the canonical
literature, but I have not re-fetched every DOI. Items marked **[free]** are openly
available; **[debated]** flags a claim where checking the source will (correctly) show
an active scholarly disagreement, not a settled fact.

### P1 — Comprehensible input / Focus on Form
- Krashen, S. (1982). *Principles and Practice in Second Language Acquisition.* Pergamon. **[free]** (PDFs at sdkrashen.com) — and Krashen (1985) *The Input Hypothesis.* **[debated]** — hugely influential, but the *i+1* construct is criticised as not precisely testable.
- Long, M. (1991). "Focus on form: A design feature in language teaching methodology." In de Bot et al. (eds.). Expanded in Long (2015), *Second Language Acquisition and Task-Based Language Teaching.*
- Nation, I.S.P. (2009). *Teaching ESL/EFL Reading and Writing*; Day & Bamford (1998), *Extensive Reading in the Second Language Classroom* — the extensive-reading / graded-reader evidence base.

### P2 — Output, Noticing, Generation
- Swain, M. (1985). "Communicative competence: some roles of comprehensible input and comprehensible output." In Gass & Madden (eds.), *Input in Second Language Acquisition.* (Output Hypothesis.)
- Schmidt, R. (1990). "The role of consciousness in second language learning." *Applied Linguistics* 11(2), 129–158. (Noticing Hypothesis.)
- Slamecka, N. & Graf, P. (1978). "The generation effect: delineation of a phenomenon." *J. Experimental Psychology: Human Learning & Memory.*

### P3 — Focused corrective feedback
- Truscott, J. (1996). "The case against grammar correction in L2 writing classes." *Language Learning* 46(2), 327–369. DOI [10.1111/j.1467-1770.1996.tb01238.x](https://doi.org/10.1111/j.1467-1770.1996.tb01238.x). **[debated]** — the *against* side; read it first to see the real controversy. (See also the 25-years-on interview: [Springer 2021](https://link.springer.com/article/10.1186/s40862-021-00110-9).)
- Ferris, D. (2011). *Treatment of Error in Second Language Student Writing* (2nd ed.), Univ. of Michigan Press; Bitchener, J. & Ferris, D. (2012), *Written Corrective Feedback in SLA and Writing* — the *for, but focused* side.
- Hattie, J. & Timperley, H. (2007). "The power of feedback." *Review of Educational Research* 77(1), 81–112. DOI [10.3102/003465430298487](https://doi.org/10.3102/003465430298487). (feed-up / feed-back / feed-forward.)
- **Meta-analytic evidence:** Chen & Renandya (2020), "Efficacy of Written Corrective Feedback in Writing Instruction: A Meta-Analysis," *TESL-EJ* 24(3) — overall **g ≈ 0.59** across 35 studies ([tesl-ej.org](https://tesl-ej.org/wordpress/issues/volume24/ej95/ej95a3/)). **[debated]** — weight of evidence favours *focused* CF on *treatable* errors; effect sizes and transfer are still argued.

### P4 — Spaced retrieval, interleaving, scheduling
- Roediger, H. & Karpicke, J. (2006). "Test-enhanced learning: taking memory tests improves long-term retention." *Psychological Science* 17(3), 249–255. DOI [10.1111/j.1467-9280.2006.01693.x](https://doi.org/10.1111/j.1467-9280.2006.01693.x). (Testing effect.)
- Bjork, R. & Bjork, E. (2011). "Making things hard on yourself, but in a good way: creating desirable difficulties." In *Psychology and the Real World.*
- Cepeda, N. et al. (2006). "Distributed practice in verbal recall tasks." *Psychological Bulletin* 132(3). (Spacing-effect meta-analysis.)
- **FSRS (Free Spaced Repetition Scheduler)** — open-source, by Jarrett Ye & the open-spaced-repetition community; **Anki's default scheduler since v23.10 (Nov 2023)**, replacing SM-2. Uses the **DSR (Difficulty–Stability–Retrievability)** memory model. Code: [github.com/open-spaced-repetition/free-spaced-repetition-scheduler](https://github.com/open-spaced-repetition/free-spaced-repetition-scheduler) **[free]**. Papers: Ye et al., "A Stochastic Shortest Path Algorithm for Optimizing Spaced Repetition Scheduling" (ACM KDD) and "Optimizing Spaced Repetition Schedule by Capturing the Dynamics of Memory" (IEEE TKDE). The concrete, modern scheduler to adopt.

### P5 — Motivation, mastery, flow
- Deci, E. & Ryan, R. (2000). "The 'what' and 'why' of goal pursuits: human needs and the self-determination of behavior." *Psychological Inquiry* 11(4), 227–268. DOI [10.1207/S15327965PLI1104_01](https://doi.org/10.1207/S15327965PLI1104_01). **[free]** overview at [selfdeterminationtheory.org](https://selfdeterminationtheory.org). (Autonomy/competence/relatedness; overjustification effect.)
- Bloom, B. (1984). "The 2 Sigma Problem: the search for methods of group instruction as effective as one-to-one tutoring." *Educational Researcher* 13(6), 4–16. DOI [10.3102/0013189X013006004](https://doi.org/10.3102/0013189X013006004). **[debated]** — the 2-σ figure is famous and aspirational; exact replicability is contested ([Wikipedia overview](https://en.wikipedia.org/wiki/Bloom's_2_sigma_problem)).
- Csíkszentmihályi, M. (1990). *Flow: The Psychology of Optimal Experience.*

### P6 — Adapt to the individual (ZPD, dynamic assessment, AI tutoring)
- Vygotsky, L. (1978). *Mind in Society.* (Zone of Proximal Development.)
- Poehner, M. & Lantolf, J. (2005). "Dynamic assessment in the language classroom." *Language Teaching Research.*
- Ellis, R. (2003). *Task-based Language Learning and Teaching* (TBLT, Phase 3).
- AI-tutoring efficacy is moving fast (2024–2026) — treat any single study as provisional and re-check yearly.

### Standards
- **CEFR Companion Volume (2020)**, Council of Europe **[free]** ([coe.int](https://www.coe.int/en/web/common-european-framework-reference-languages)) — the authoritative source for level descriptors, can-do statements, and mediation. Use this for the level→competence mapping rather than ad-hoc lists.

### Latest evidence (2024–2026) — re-checked, with links

*AI/LLM tutoring evidence moves fast; treat any single study as provisional.*

- **LLMs drift off the target CEFR level** — directly relevant to our biggest open risk (story generation): "Alignment Drift in CEFR-prompted LLMs for Interactive Spanish Tutoring," arXiv [2505.08351](https://arxiv.org/abs/2505.08351) (2025). Empirical confirmation that prompting an LLM to "write at A2" is *not* reliable — it validates building a "stays-in-level" checker rather than trusting the prompt.
- **AI in language teaching — positive across skills:** "Effectiveness of Artificial Intelligence (AI) in language teaching," *Computers & Education: AI* (2025), [ScienceDirect S2666920X25001626](https://www.sciencedirect.com/science/article/pii/S2666920X25001626). Reports positive effects across vocabulary, reading, writing, listening, speaking — with large variation by level and design.
- **LLMs in education — systematic reviews (2025):** [ScienceDirect S2666920X25001699](https://www.sciencedirect.com/science/article/pii/S2666920X25001699) and Springer [10.1007/s43621-025-01094-z](https://link.springer.com/article/10.1007/s43621-025-01094-z) (personalised learning).
- **Self-regulation caution:** meta-analysis of LLM effects on students, arXiv [2509.22725](https://arxiv.org/abs/2509.22725) (2025) — *near-zero* benefit to self-regulation (most studies ≤10 weeks). Reinforces **P5**: don't assume the tool builds study habits; design for them (FSRS cadence, reflection) and measure over months.
- **Online feedback meta-analysis:** teacher online feedback (g ≈ 2.25) ≫ automated (g ≈ 0.70) ≫ peer — *The Asia-Pacific Education Researcher*, [Springer 10.1007/s40299-021-00594-6](https://link.springer.com/article/10.1007/s40299-021-00594-6). Honest signal: automated feedback (what we ship) helps, but is **not** as strong as a good human teacher — frame Plappo as *scalable practice between lessons*, not a teacher replacement.
- **Recent feedback synthesis (2024):** "How effective is feedback for L1, L2, and FL learners' writing? A meta-analysis," *Assessing Writing* / *J. Second Language Writing*, [ScienceDirect S0959475224000884](https://www.sciencedirect.com/science/article/pii/S0959475224000884).

> **Honesty note:** the *core* findings (retrieval practice, spacing, output, focused feedback on rule-based errors) are robust and replicated. The headline *figures* and *strong* versions — Krashen's *i+1*, Bloom's exact 2σ, "correction always works" — are influential but debated. That's precisely why the sources are here: so the team checks them and builds on the solid parts. Core SLA is stable; FSRS internals, CEFR editions, and AI-tutoring evidence evolve — revisit Phase 1/4 yearly.
