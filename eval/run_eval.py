"""Run the German grammar-feedback eval and print a report.

Usage:
    python run_eval.py --mock              # no API key; verifies the harness
    python run_eval.py                     # live; needs ANTHROPIC_API_KEY
    python run_eval.py --limit 6           # first 6 cases only
    GERMAN_TUTOR_MODEL=claude-sonnet-4-6 python run_eval.py

Writes the full per-case + aggregate result to results/<timestamp>.json.
"""

import argparse
import json
import os
import sys
import time
from datetime import datetime, timezone

from dataset import CASES, summary
import score


def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("--mock", action="store_true",
                   help="Use the deterministic mock tutor (no API key needed).")
    p.add_argument("--limit", type=int, default=None,
                   help="Only run the first N cases.")
    return p.parse_args()


def main():
    # Windows consoles default to cp1252; force UTF-8 so German + dashes render.
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:  # noqa: BLE001
        pass
    args = parse_args()
    cases = CASES[: args.limit] if args.limit else CASES

    if args.mock:
        import mock_tutor as engine
        client = None
        model = "MOCK"
    else:
        import tutor as engine
        try:
            client = engine.build_client()
        except Exception as e:  # noqa: BLE001
            sys.exit(f"Could not init Anthropic client: {e}\n"
                     "Set ANTHROPIC_API_KEY, or run with --mock.")
        model = engine.MODEL

    print(f"Model: {model}   Cases: {len(cases)}")
    print("Running", end="", flush=True)

    results = []
    records = []
    for c in cases:
        t0 = time.time()
        fb = engine.get_feedback(client, c.level, c.text)
        dt = time.time() - t0
        r = score.score_case(c, fb)
        results.append(r)
        records.append({
            "id": c.id, "level": c.level, "text": c.text,
            "gold_correct": c.corrected, "gold_cats": [e.value for e in c.errors],
            "pred_corrected": fb.corrected_sentence,
            "pred_cats": [e.category.value for e in fb.errors],
            "pred_has_errors": fb.has_errors,
            "correction_ok": r.correction_ok, "latency_s": round(dt, 2),
        })
        print(".", end="", flush=True)
    print(" done.\n")

    agg = score.aggregate(results)
    print_report(agg, results)

    out_dir = os.path.join(os.path.dirname(__file__), "results")
    os.makedirs(out_dir, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    path = os.path.join(out_dir, f"{model}_{stamp}.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump({"model": model, "aggregate": agg, "cases": records},
                  f, ensure_ascii=False, indent=2)
    print(f"\nFull results written to {path}")


def print_report(agg, results):
    d = agg["detection"]
    c = agg["category"]
    corr = agg["correction"]

    print("=" * 64)
    print("GERMAN GRAMMAR FEEDBACK — EVAL REPORT")
    print("=" * 64)
    print(f"{agg['n_cases']} cases  "
          f"({agg['n_error_sentences']} with errors, "
          f"{agg['n_correct_sentences']} already correct)\n")

    print("1) ERROR DETECTION (does it spot a problem at all?)")
    print(f"   recall   {d['recall']:.0%}  ({d['errors_caught']} caught, {d['errors_missed']} missed)")
    print(f"   precision{d['precision']:>5.0%}")
    print(f"   >> FALSE-POSITIVE RATE on correct sentences: "
          f"{d['false_positive_rate_on_correct']:.0%} "
          f"({d['invented_errors']} invented)   [the trust metric]")
    print(f"   clean-pass rate on correct sentences: {d['clean_pass_rate']:.0%}\n")

    print("2) CATEGORY (is the *kind* of error right?)")
    print(f"   micro P/R/F1: {c['precision']:.0%} / {c['recall']:.0%} / {c['f1']:.2f}"
          f"   (tp={c['tp']} fp={c['fp']} fn={c['fn']})\n")

    print("3) CORRECTION (does the rewrite match the canonical fix?)")
    print(f"   accuracy on error sentences:     {corr['accuracy_on_error_sentences']:.0%}")
    print(f"   left correct sentences unchanged:{corr['unchanged_on_correct_sentences']:>5.0%}\n")

    print("4) BY LEVEL")
    for lvl, s in agg["by_level"].items():
        ca = "n/a" if s["correction_acc"] is None else f"{s['correction_acc']:.0%}"
        print(f"   {lvl}: detect-F1 {s['detect_f1']:.2f}  "
              f"correction {ca}  "
              f"false-pos {s['false_positives']}/{s['n_correct']}")
    print()

    # per-case failures
    fails = [r for r in results
             if (not r.is_correct and (not r.pred_has_errors or r.gold_cats != r.pred_cats or not r.correction_ok))
             or (r.is_correct and r.pred_has_errors)]
    if fails:
        print("FLAGGED CASES (something off):")
        for r in fails:
            tags = []
            if r.is_correct and r.pred_has_errors:
                tags.append("INVENTED-ERROR")
            if not r.is_correct and not r.pred_has_errors:
                tags.append("MISSED")
            if not r.is_correct and r.pred_has_errors and r.gold_cats != r.pred_cats:
                tags.append(f"CAT {sorted(x.value for x in r.gold_cats)}!={sorted(x.value for x in r.pred_cats)}")
            if not r.is_correct and not r.correction_ok:
                tags.append("BAD-CORRECTION")
            print(f"   {r.case_id} [{r.level}] {'  '.join(tags)}")
    else:
        print("No flagged cases — clean run.")


if __name__ == "__main__":
    main()
