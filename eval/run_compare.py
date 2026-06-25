"""Run the eval against multiple Vertex/Gemini models and print a side-by-side.

Same dataset, prompt, schema, and scorer for every model — so the comparison is
apples-to-apples. Defaults to Gemini 2.5 Pro vs Flash (yavar's two models).

    python run_compare.py
    python run_compare.py gemini-2.5-flash gemini-2.5-pro
"""

import json
import os
import sys
import time
from datetime import datetime, timezone

from dataset import CASES
import score
from vertex_backend import VertexGeminiTutor

DEFAULT_MODELS = ["gemini-2.5-pro", "gemini-2.5-flash"]


def run_model(model_id, cases):
    tutor = VertexGeminiTutor(model_id)
    results, records, errors, total_lat = [], [], 0, 0.0
    print(f"\n[{model_id}] running {len(cases)} cases ", end="", flush=True)
    for c in cases:
        t0 = time.time()
        try:
            fb = tutor.get_feedback(c.level, c.text)
            mark = "."
        except Exception as e:  # noqa: BLE001
            from tutor import TutorFeedback
            fb = TutorFeedback(has_errors=False, corrected_sentence=c.text, errors=[])
            errors += 1
            mark = "x"
            print(f"\n  ! {c.id}: {e}", end="")
        dt = time.time() - t0
        total_lat += dt
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
        print(mark, end="", flush=True)
    print(f" done ({total_lat:.0f}s, {errors} call errors)")
    agg = score.aggregate(results)
    return {"model": model_id, "aggregate": agg, "cases": records,
            "call_errors": errors, "avg_latency_s": round(total_lat / len(CASES), 2)}


def pct(x):
    return "  n/a" if x is None else f"{x:>5.0%}"


def print_compare(runs):
    rows = [
        ("Detection recall (errors caught)", lambda a: a["detection"]["recall"]),
        ("Detection precision", lambda a: a["detection"]["precision"]),
        (">> False-pos rate on CORRECT  (lower=better)", lambda a: a["detection"]["false_positive_rate_on_correct"]),
        ("Clean-pass rate on correct", lambda a: a["detection"]["clean_pass_rate"]),
        ("Category F1", lambda a: a["category"]["f1"]),
        ("Correction acc (error sentences)", lambda a: a["correction"]["accuracy_on_error_sentences"]),
    ]
    names = [r["model"] for r in runs]
    w = 38
    print("\n" + "=" * (w + 14 * len(names)))
    print("PRO vs FLASH — German grammar feedback (Vertex/Gemini)")
    print("=" * (w + 14 * len(names)))
    n_err = runs[0]["aggregate"]["n_error_sentences"]
    n_cor = runs[0]["aggregate"]["n_correct_sentences"]
    print(f"{n_err + n_cor} cases: {n_err} with errors, {n_cor} already correct\n")
    header = f"{'metric':<{w}}" + "".join(f"{n.split('-')[-1]:>14}" for n in names)
    print(header)
    print("-" * len(header))
    for label, fn in rows:
        line = f"{label:<{w}}"
        for r in runs:
            v = fn(r["aggregate"])
            if isinstance(label, str) and "F1" in label:
                line += f"{('  n/a' if v is None else f'{v:>6.2f}'):>14}"
            else:
                line += f"{pct(v):>14}"
        print(line)
    print("-" * len(header))
    line = f"{'avg latency / call':<{w}}"
    for r in runs:
        line += f"{r['avg_latency_s']:>13}s"
    print(line)
    line = f"{'call errors':<{w}}"
    for r in runs:
        line += f"{r['call_errors']:>14}"
    print(line)

    # Per-level false positives, the trust-killer to watch
    print("\nFalse positives on correct sentences, by level:")
    for r in runs:
        bl = r["aggregate"]["by_level"]
        fp = "  ".join(f"{lvl}:{bl[lvl]['false_positives']}/{bl[lvl]['n_correct']}" for lvl in bl)
        print(f"  {r['model']:<18} {fp}")

    # Disagreements: where the two models differ on a case
    if len(runs) == 2:
        a, b = runs
        amap = {c["id"]: c for c in a["cases"]}
        bmap = {c["id"]: c for c in b["cases"]}
        diffs = []
        for cid in amap:
            ca, cb = amap[cid], bmap[cid]
            if (ca["pred_has_errors"] != cb["pred_has_errors"]
                    or ca["correction_ok"] != cb["correction_ok"]
                    or set(ca["pred_cats"]) != set(cb["pred_cats"])):
                diffs.append((cid, ca, cb))
        if diffs:
            print(f"\nDisagreements ({len(diffs)}):  [✓/✗ = correction matched gold]")
            for cid, ca, cb in diffs:
                gold = "CORRECT" if not ca["gold_cats"] else ",".join(ca["gold_cats"])
                print(f"  {cid} [{ca['level']}] gold={gold}")
                print(f"      {a['model']:<16} {'✓' if ca['correction_ok'] else '✗'} "
                      f"cats={ca['pred_cats']}  -> {ca['pred_corrected']!r}")
                print(f"      {b['model']:<16} {'✓' if cb['correction_ok'] else '✗'} "
                      f"cats={cb['pred_cats']}  -> {cb['pred_corrected']!r}")


def main():
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:  # noqa: BLE001
        pass
    args = sys.argv[1:]
    levels = None
    for a in list(args):
        if a.startswith("--levels="):
            levels = {x.strip().upper() for x in a.split("=", 1)[1].split(",")}
            args.remove(a)
    models = args or DEFAULT_MODELS
    cases = [c for c in CASES if not levels or c.level in levels]
    print(f"Filtered to {len(cases)} cases" + (f" (levels {sorted(levels)})" if levels else ""))
    runs = [run_model(m, cases) for m in models]
    print_compare(runs)

    out_dir = os.path.join(os.path.dirname(__file__), "results")
    os.makedirs(out_dir, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    path = os.path.join(out_dir, f"compare_{stamp}.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump({"models": models, "runs": runs}, f, ensure_ascii=False, indent=2)
    print(f"\nFull results: {path}")


if __name__ == "__main__":
    main()
