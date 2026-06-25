# Manual QA checklist (prototype)

The invisible-close-button bug shipped because no one clicked through the exit
paths end-to-end. This checklist exists so core flows get exercised after changes.
Run it in a browser at <http://127.0.0.1:8000> (and the `?demo=1` variant).

## Automated (run before manual)
- [ ] `cd eval && python run_eval.py --mock` — grammar harness + schema back-compat.
- [ ] `python skills_demonstrated_eval.py --mock` — `demonstrated` self-consistency.
- [ ] `python -c "import story_service, vocab_coverage, vertex_backend, tutor"` — imports.
- [ ] Server up: `GET /` 200, `POST /api/story {level}` 200, `POST /api/feedback {sentence:""}` 400.
- [ ] (with creds) `python skills_demonstrated_eval.py` live — **contradiction rate 0**,
      advanced over-claim ~0, before trusting the measured level.

## First run (honest cold start)
- [ ] Fresh `localStorage` (or incognito): header shows **🔥 0**, no due badge.
- [ ] Learn tab shows the "New here? Let's measure your level" cue, not fake weak spots.
- [ ] Profile shows A1, zero skills, vocab 0.
- [ ] `?demo=1` loads populated data (streak/skills/reviews) and is clearly the demo.

## Reading + glossary
- [ ] Open a story; tap a glossed (highlighted) word → sheet shows gloss.
- [ ] Tab to a glossed word and press Enter/Space → sheet opens (keyboard a11y).
- [ ] Looking a word up does **not** add it to reviews; "+ Add to review" does.
- [ ] After revisiting a word, the button reads "seen N×"; tapping shows "✓ In your reviews".
- [ ] Progress dots advance as you scroll; all lit when the story fits/▼ bottom reached.
- [ ] No audio plays unless you press 🔊 / "Hear it".
- [ ] Offline (stop generation): a previously read story is reused, not always the same fallback.

## Answer → feedback (needs VERTEX_PROJECT)
- [ ] First question is the **✍️ Task** (communicative), then comprehension questions.
- [ ] Submit German with one error → focused card: struck error + fix, one chip, rest collapsed.
- [ ] Praise names a real strength (or neutral), never a random compliment.
- [ ] "Drill this" builds **your own corrected sentence** to reorder.
- [ ] After feedback, a matching cloze appears in **Review**.
- [ ] Profile: only the exercised skill(s) move; a simple correct sentence does **not**
      bump advanced skills.

## Review (verified recall)
- [ ] Start review → type the answer → **Check**: correct/✗ shown, answer revealed.
- [ ] Suggested grade is highlighted (correct+fast = Easy); manual override works.
- [ ] "Show answer" reveals without typing and lets you self-grade.
- [ ] Finish → summary + next-due interval.

## Navigation (the regression that started this)
- [ ] Exit a review session via the **×** (top-left).
- [ ] Exit story / drill / practice via their **×**.
- [ ] On Review/Profile tabs the **‹** back arrow returns to Learn; hidden on Learn.
- [ ] Bottom tab bar switches Learn / Review / Profile everywhere.
