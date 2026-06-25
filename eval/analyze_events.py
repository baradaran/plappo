"""Offline analysis of the consented event log (prototype/data/events.jsonl).

Turns the no-PII events into the things we actually want them for:
  - FSRS optimisation readiness + a scheduler **calibration** check (predicted vs
    actual recall) and an exported review log an optimiser can train on
  - judge / content-gate calibration from real story generations
  - feedback-engine usage summaries

No network, no LLM — reads only the fields the client logged (see docs/PRIVACY.md).

    python analyze_events.py
    python analyze_events.py --path some/events.jsonl --write-log
"""

import argparse
import csv
import json
import os
from collections import Counter, defaultdict

DECAY, FACTOR = -0.5, 19 / 81           # same forgetting curve as the client FSRS
DEFAULT = os.path.join(os.path.dirname(__file__), "..", "prototype", "data", "events.jsonl")


def retr(S, t):
    return (1 + FACTOR * t / S) ** DECAY if S > 0 else 0.0


def load(path):
    out = []
    try:
        with open(path, encoding="utf-8") as f:
            for ln in f:
                ln = ln.strip()
                if ln:
                    out.append(json.loads(ln))
    except OSError:
        pass
    return out


def pct(n, d):
    return f"{(100*n/d):.0f}%" if d else "—"


def section(t):
    print("\n" + "=" * 60 + f"\n{t}\n" + "=" * 60)


def analyze_reviews(reviews, write_log):
    section(f"FSRS — review log ({len(reviews)} reviews)")
    if not reviews:
        print("no review events yet.")
        return
    users = {r.get("id") for r in reviews}
    seqs = defaultdict(list)                       # (user, card) -> reviews
    for r in reviews:
        seqs[(r.get("id"), (r.get("payload") or {}).get("card"))].append(r)
    lens = [len(v) for v in seqs.values()]
    print(f"learners: {len(users)}   cards: {len(seqs)}   "
          f"cards with >=2 reviews: {sum(l>=2 for l in lens)}   >=5: {sum(l>=5 for l in lens)}")
    grades = Counter((r.get("payload") or {}).get("grade") for r in reviews)
    print("grade distribution (1=Again..4=Easy):",
          {g: grades.get(g, 0) for g in (1, 2, 3, 4)})
    cats = Counter((r.get("payload") or {}).get("cat") for r in reviews)
    print("most-reviewed grammar points:", dict(cats.most_common(6)))

    # calibration: predicted recall (from stability BEFORE the review + elapsed) vs
    # actual outcome (success = grade>=2). Well-calibrated => predicted ≈ actual.
    pred, actual, bins = [], [], defaultdict(lambda: [0, 0])
    for r in reviews:
        p = r.get("payload") or {}
        if (p.get("reps") or 0) < 1:
            continue
        S, t = p.get("s_before"), p.get("elapsed_days")
        if not S or t is None:
            continue
        R = retr(S, max(0.0, t))
        ok = 1 if (p.get("grade") or 0) >= 2 else 0
        pred.append(R); actual.append(ok)
        b = min(9, int(R * 10)); bins[b][0] += 1; bins[b][1] += ok
    if pred:
        mp, ma = sum(pred)/len(pred), sum(actual)/len(actual)
        print(f"\ncalibration (n={len(pred)}): mean predicted recall {mp:.2f} vs "
              f"actual {ma:.2f}  (gap {abs(mp-ma):.2f}; closer is better)")
        print("  predicted-bin   n   actual recall")
        for b in sorted(bins):
            n, ok = bins[b]
            print(f"   {b/10:.1f}-{b/10+0.1:.1f}     {n:>4}   {pct(ok, n)}")
    else:
        print("\ncalibration: not enough repeat reviews yet (need cards reviewed 2+ times).")

    if write_log:
        out = os.path.join(os.path.dirname(__file__), "results", "fsrs_review_log.csv")
        os.makedirs(os.path.dirname(out), exist_ok=True)
        with open(out, "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f); w.writerow(["user", "card", "review_date", "elapsed_days", "rating"])
            for r in reviews:
                p = r.get("payload") or {}
                w.writerow([r.get("id"), p.get("card"), r.get("ts"),
                            p.get("elapsed_days"), p.get("grade")])
        print(f"\nwrote optimiser-ready review log -> {out}")


def analyze_stories(stories):
    section(f"Content gate / judge calibration ({len(stories)} stories)")
    if not stories:
        print("no story events yet.")
        return
    by = defaultdict(list)
    for s in stories:
        by[(s.get("payload") or {}).get("level")].append((s.get("payload") or {}).get("check") or {})
    src = Counter((s.get("payload") or {}).get("source") for s in stories)
    print("served from:", dict(src), "(library = no LLM call)\n")
    print(" level   n   on-band   avg cov   avg nat   avg tries")
    for lvl in sorted(k for k in by if k):
        ch = by[lvl]
        n = len(ch)
        on = sum(1 for c in ch if c.get("in_band"))
        cov = [c.get("coverage") for c in ch if c.get("coverage") is not None]
        nat = [c.get("naturalness") for c in ch if c.get("naturalness")]
        tr = [c.get("attempts") for c in ch if c.get("attempts")]
        print(f"  {lvl:<5} {n:>3}   {pct(on,n):>6}   "
              f"{(sum(cov)/len(cov) if cov else 0):.2f}     "
              f"{(sum(nat)/len(nat) if nat else 0):.1f}/5    "
              f"{(sum(tr)/len(tr) if tr else 0):.1f}")


def analyze_feedback(fb):
    section(f"Feedback engine usage ({len(fb)} answers)")
    if not fb:
        print("no feedback events yet.")
        return
    correct = sum(1 for e in fb if ((e.get("payload") or {}).get("n_errors") or 0) == 0)
    print(f"answers correct first try: {correct}/{len(fb)} ({pct(correct,len(fb))})")
    cats = Counter(c for e in fb for c in ((e.get("payload") or {}).get("cats") or []))
    demo = Counter(c for e in fb for c in ((e.get("payload") or {}).get("demonstrated") or []))
    print("most common errors      :", dict(cats.most_common(6)))
    print("most demonstrated skills:", dict(demo.most_common(6)))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--path", default=DEFAULT)
    ap.add_argument("--write-log", action="store_true", help="export an FSRS optimiser review log CSV")
    args = ap.parse_args()
    try:
        import sys; sys.stdout.reconfigure(encoding="utf-8")
    except Exception:  # noqa: BLE001
        pass

    events = load(args.path)
    print(f"loaded {len(events)} events from {args.path}")
    if not events:
        print("(no consented events yet — the file appears once a learner opts in and uses the app)")
        return
    by = defaultdict(list)
    for e in events:
        by[e.get("type")].append(e)
    analyze_reviews(by.get("review", []), args.write_log)
    analyze_stories(by.get("story", []))
    analyze_feedback(by.get("feedback", []))


if __name__ == "__main__":
    main()
