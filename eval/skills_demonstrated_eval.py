"""Validate the `demonstrated` field before the app trusts it (ADR-009, P1).

The app credits grammar-skill mastery only for constructions the learner actually
used *correctly* in a sentence — reported by the tutor in `TutorFeedback.demonstrated`.
That field is only safe to drive a "measured level" if the model:

  1. never lists a skill it also flagged as an error in the same sentence
     (a self-contradiction), and
  2. doesn't *over-claim* — e.g. assert an advanced construction (Passiv,
     Konjunktiv I, …) on a simple correct A1/A2 sentence that never used it.

This eval measures both, plus how often the model returns *something* on correct
sentences (coverage) so the signal isn't uselessly empty. Run it before relying on
`demonstrated` to move skill bars.

Usage:
    python skills_demonstrated_eval.py --mock     # no creds; verifies mechanics
    python skills_demonstrated_eval.py            # live; needs Vertex (gcloud ADC + VERTEX_PROJECT)
    python skills_demonstrated_eval.py --model gemini-2.5-flash
"""

import argparse
import json
import os
import sys
from datetime import datetime, timezone

from dataset import CASES

# Constructions that should essentially never be "demonstrated" on a simple
# correct A1/A2 sentence — these are the over-claims that would let a beginner
# falsely "master" advanced grammar.
ADVANCED = {"PASSIVE", "SUBJUNCTIVE_I", "SUBJUNCTIVE_II", "NOMINALIZATION",
            "PARTICIPIAL", "MODAL_PARTICLE", "RELATIVE_CLAUSE"}


def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("--mock", action="store_true", help="Deterministic mock (no creds).")
    p.add_argument("--model", default=None, help="Vertex model id (live runs).")
    p.add_argument("--limit", type=int, default=None)
    return p.parse_args()


def main():
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:  # noqa: BLE001
        pass
    args = parse_args()
    cases = CASES[: args.limit] if args.limit else CASES

    if args.mock:
        import mock_tutor
        get = lambda lvl, txt: mock_tutor.get_feedback(None, lvl, txt)  # noqa: E731
        model = "MOCK"
    else:
        from vertex_backend import VertexGeminiTutor
        engine = VertexGeminiTutor(args.model or "gemini-2.5-flash")
        get = lambda lvl, txt: engine.get_feedback(lvl, txt)  # noqa: E731
        model = engine.model_id

    print(f"Model: {model}   Cases: {len(cases)}")
    print("Running", end="", flush=True)

    records, contradictions, overclaims = [], 0, 0
    n_error_cases = 0
    correct_with_any, correct_total, demonstrated_on_correct = 0, 0, 0
    for c in cases:
        fb = get(c.level, c.text)
        dem = [d.value for d in fb.demonstrated]
        errc = {e.category.value for e in fb.errors}
        contra = sorted(set(dem) & errc)          # listed as both right and wrong
        if c.errors:
            n_error_cases += 1
        if contra:
            contradictions += 1
        over = []
        if c.is_correct:
            correct_total += 1
            demonstrated_on_correct += len(dem)
            if dem:
                correct_with_any += 1
            if c.level in ("A1", "A2"):
                over = sorted(set(dem) & ADVANCED)
                if over:
                    overclaims += 1
        records.append({"id": c.id, "level": c.level, "is_correct": c.is_correct,
                        "demonstrated": dem, "contradiction": contra, "overclaim": over})
        print(".", end="", flush=True)
    print(" done.\n")

    n_a12_correct = sum(1 for c in cases if c.is_correct and c.level in ("A1", "A2"))
    agg = {
        "n_cases": len(cases),
        "contradiction_rate": round(contradictions / max(1, len(cases)), 3),
        "advanced_overclaim_rate_on_A1A2_correct": round(overclaims / max(1, n_a12_correct), 3),
        "coverage_on_correct": round(correct_with_any / max(1, correct_total), 3),
        "mean_demonstrated_on_correct": round(demonstrated_on_correct / max(1, correct_total), 2),
        "contradictions": contradictions,
        "overclaims": overclaims,
    }

    print("=" * 60)
    print("DEMONSTRATED-SKILLS EVAL")
    print("=" * 60)
    print(f"contradiction rate (demonstrated ∩ errors):   {agg['contradiction_rate']:.0%}"
          "   [must be 0]")
    print(f"advanced over-claim on A1/A2 correct:          "
          f"{agg['advanced_overclaim_rate_on_A1A2_correct']:.0%}   [must be ~0]")
    print(f"coverage on correct sentences (≥1 listed):     {agg['coverage_on_correct']:.0%}")
    print(f"mean demonstrated per correct sentence:        {agg['mean_demonstrated_on_correct']}\n")

    flagged = [r for r in records if r["contradiction"] or r["overclaim"]]
    if flagged:
        print("FLAGGED CASES:")
        for r in flagged:
            tag = []
            if r["contradiction"]:
                tag.append(f"CONTRADICTION {r['contradiction']}")
            if r["overclaim"]:
                tag.append(f"OVER-CLAIM {r['overclaim']}")
            print(f"   {r['id']} [{r['level']}] {'  '.join(tag)}")
    else:
        print("No flagged cases — demonstrated field is self-consistent.")

    out_dir = os.path.join(os.path.dirname(__file__), "results")
    os.makedirs(out_dir, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    path = os.path.join(out_dir, f"demonstrated_{model}_{stamp}.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump({"model": model, "aggregate": agg, "cases": records},
                  f, ensure_ascii=False, indent=2)
    print(f"\nFull results written to {path}")


if __name__ == "__main__":
    main()
