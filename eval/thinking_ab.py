"""A/B the tutor's thinking budget: does cutting it keep grammar quality while
cutting latency? (Follow-up to surfacing feedback latency.)

Runs the SAME grammar dataset through the SAME model at several thinking budgets
(unset = provider default, 0 = off, or a cap), scoring each with the normal
scorer and timing each call. Prints quality (detection recall, the false-positive
trust metric) alongside latency, so we only lower the default if quality holds.

Usage:
    python thinking_ab.py                       # budgets: default vs 0, all cases
    python thinking_ab.py --budgets ,0,128 --limit 16
    python thinking_ab.py --model gemini-2.5-flash
Needs Vertex creds (gcloud ADC + VERTEX_PROJECT or a local .env).
"""

import argparse
import os
import statistics
import sys
import time

from dataset import CASES
import score


def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("--model", default="gemini-2.5-flash")
    p.add_argument("--budgets", default=",0",
                   help="Comma-separated budgets; empty item = provider default. e.g. ',0,128'")
    p.add_argument("--limit", type=int, default=None, help="First N cases (cost control).")
    return p.parse_args()


def run_budget(engine, cases, budget):
    # budget: "" -> unset (default thinking); else string int
    if budget == "":
        os.environ.pop("TUTOR_THINKING_BUDGET", None)
    else:
        os.environ["TUTOR_THINKING_BUDGET"] = budget
    results, lats = [], []
    for c in cases:
        t0 = time.perf_counter()
        fb = engine.get_feedback(c.level, c.text)
        lats.append(time.perf_counter() - t0)
        results.append(score.score_case(c, fb))
        print(".", end="", flush=True)
    return score.aggregate(results), lats


def main():
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:  # noqa: BLE001
        pass
    args = parse_args()
    from vertex_backend import VertexGeminiTutor
    engine = VertexGeminiTutor(args.model)
    cases = CASES[: args.limit] if args.limit else CASES
    budgets = args.budgets.split(",")

    rows = []
    for b in budgets:
        label = "default" if b == "" else f"budget={b}"
        print(f"\n[{label}] running {len(cases)} cases", end="", flush=True)
        agg, lats = run_budget(engine, cases, b)
        lats_ms = sorted(round(x * 1000) for x in lats)
        rows.append((label, agg, lats_ms))
        print(" done.")

    print("\n" + "=" * 72)
    print(f"THINKING-BUDGET A/B  ({args.model}, {len(cases)} cases)")
    print("=" * 72)
    print(f"{'variant':<12}{'recall':>8}{'falsePos':>10}{'cleanPass':>11}"
          f"{'median ms':>11}{'p90 ms':>9}")
    for label, agg, lats_ms in rows:
        d = agg["detection"]
        med = statistics.median(lats_ms) if lats_ms else 0
        p90 = lats_ms[max(0, int(len(lats_ms) * 0.9) - 1)] if lats_ms else 0
        print(f"{label:<12}{d['recall']:>7.0%}"
              f"{d['false_positive_rate_on_correct']:>10.0%}"
              f"{d['clean_pass_rate']:>11.0%}{med:>11.0f}{p90:>9}")
    print("\nLower the default only if a reduced budget keeps recall and a 0% "
          "false-positive rate (the trust metric).")


if __name__ == "__main__":
    main()
