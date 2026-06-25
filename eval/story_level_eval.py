"""Story-in-level eval: does a generated German story land ON its target CEFR
level — not above it (drift) and not below it (too easy)?

This operationalises the input-side risk (arXiv 2505.08351, 2025: LLMs drift off
a prompted CEFR level). But "don't exceed the level" is only half the job — input
that's *too easy* breaks i+1 just as surely. So we classify every story three ways:

  ABOVE  — judged above target, or contains words/grammar above target  (drift)
  ON     — judged at target, no over-level leaks                        (ship it)
  BELOW  — judged below target                                          (too easy)

Method: GENERATE with one model (default Flash — what we'd ship), JUDGE with a
DIFFERENT model (default Pro) acting as a strict CEFR examiner, to avoid a model
grading its own work too kindly.

Honest limits: the judge is itself an LLM, imperfect at CEFR. This is a drift
*signal* and a generator comparison, not a certified grade. For production,
calibrate the judge against human ratings and/or a real level word-list (Goethe).

    python story_level_eval.py
    python story_level_eval.py --levels A2,B1,B2 --sentences 12
    python story_level_eval.py --gen gemini-2.5-pro
"""

import argparse
import json
import os
import sys
import time
from datetime import datetime, timezone

from vertex_backend import vertex_json
from vocab_coverage import coverage as lexical_coverage

ORDER = ["A1", "A2", "B1", "B2", "C1", "C2"]
TOPICS = ["der erste Schultag", "ein verlorener Hund im Park"]

GEN_SCHEMA = {
    "type": "OBJECT",
    "properties": {"title": {"type": "STRING"},
                   "sentences": {"type": "ARRAY", "items": {"type": "STRING"}}},
    "required": ["title", "sentences"],
}
JUDGE_SCHEMA = {
    "type": "OBJECT",
    "properties": {
        "estimated_cefr": {"type": "STRING", "enum": ORDER},
        "over_level_words": {"type": "ARRAY", "items": {"type": "STRING"}},
        "over_level_grammar": {"type": "ARRAY", "items": {"type": "STRING"}},
        "stays_in_level": {"type": "BOOLEAN"},
        # ADR-022: naturalness is a SEPARATE axis from level. 1=stilted textbook /
        # translationese, 5=reads like a native actually wrote it.
        "naturalness": {"type": "INTEGER"},
        "unnatural_phrases": {"type": "ARRAY", "items": {"type": "STRING"}},
        "note": {"type": "STRING"},
    },
    "required": ["estimated_cefr", "over_level_words", "over_level_grammar",
                 "stays_in_level", "naturalness", "unnatural_phrases", "note"],
}


def gen_system(level):
    return (f"You write short stories in German for language learners at exactly CEFR level "
            f"{level}. Use ONLY vocabulary and grammar appropriate to {level}, but make the story "
            f"genuinely engaging and rich enough to be worth a {level} learner's time — hit the "
            f"level, do not undershoot it and do not exceed it.")


def judge_system(level):
    return (f"You are a strict CEFR examiner AND a native German speaker. The text was written for a "
            f"learner at level {level}. (1) List any words clearly above {level} and any grammar clearly "
            f"above {level}; give your overall CEFR estimate; stays_in_level=true ONLY if nothing is "
            f"clearly above {level} (be conservative — don't flag words a {level} learner would know). "
            f"(2) Rate naturalness 1-5: 5 = reads exactly like German a native would actually write; "
            f"1 = stilted textbook or translated-from-English German. Naturalness is SEPARATE from "
            f"level — simple, low-level words can be perfectly natural. List any unnatural / "
            f"translationese phrases that hurt the score.")


def generate(model, level, topic, n):
    out = vertex_json(model, gen_system(level),
                      f"Write a {n}-sentence story at level {level}. Topic: {topic}.",
                      GEN_SCHEMA, temperature=0.7)
    return out.get("title", ""), out.get("sentences", [])


def judge(model, level, text):
    return vertex_json(model, judge_system(level),
                       f"Target level: {level}\n\nText:\n{text}", JUDGE_SCHEMA, temperature=0.0)


def classify(target, j):
    """Return 'above' | 'on' | 'below'."""
    est = j.get("estimated_cefr")
    over = bool(j.get("over_level_words") or j.get("over_level_grammar")) or (j.get("stays_in_level") is False)
    if est not in ORDER:
        return "above" if over else "on"
    ti, ei = ORDER.index(target), ORDER.index(est)
    if ei > ti or over:
        return "above"
    if ei < ti:
        return "below"
    return "on"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--gen", default="gemini-2.5-flash")
    ap.add_argument("--judge", default="gemini-2.5-pro")
    ap.add_argument("--levels", default="A1,A2,B1")
    ap.add_argument("--sentences", type=int, default=5)
    args = ap.parse_args()
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:  # noqa: BLE001
        pass
    levels = [x.strip().upper() for x in args.levels.split(",")]

    print(f"generator: {args.gen}   judge: {args.judge}   length: {args.sentences} sentences")
    print(f"{len(levels)}×{len(TOPICS)} = {len(levels)*len(TOPICS)} stories\n")

    records = {"above": 0, "on": 0, "below": 0}
    rows = []
    for level in levels:
        for topic in TOPICS:
            t0 = time.time()
            title, sents = generate(args.gen, level, topic, args.sentences)
            text = " ".join(sents)
            j = judge(args.judge, level, text)
            cls = classify(level, j)
            records[cls] += 1
            ow, og = j.get("over_level_words", []), j.get("over_level_grammar", [])
            cov = lexical_coverage(text, level)   # deterministic lexical check (ADR-019)
            nat = j.get("naturalness") or 0       # naturalness axis (ADR-022)
            rows.append({"target": level, "topic": topic, "title": title, "text": text,
                         "estimated": j.get("estimated_cefr"), "class": cls,
                         "over_words": ow, "over_grammar": og, "coverage": cov["coverage"],
                         "naturalness": nat, "unnatural_phrases": j.get("unnatural_phrases", []),
                         "note": j.get("note", ""), "latency_s": round(time.time() - t0, 1)})
            mark = {"above": "DRIFT↑", "on": "ON   ", "below": "EASY↓"}[cls]
            extra = f" · over: {', '.join(ow[:5])}" if ow else ""
            print(f"  [{mark}] target {level} · est {j.get('estimated_cefr'):<2} · "
                  f"cov {cov['coverage']:.0%} · nat {nat}/5 · {topic}{extra}")

    n = sum(records.values())
    print("\n" + "=" * 60)
    print("STORY-IN-LEVEL — landing report")
    print("=" * 60)
    print(f"ON band (ship): {records['on']}/{n} = {records['on']/n:.0%}")
    print(f"  ↑ above (drift / too hard): {records['above']}/{n}")
    print(f"  ↓ below (too easy):         {records['below']}/{n}")
    nats = [r["naturalness"] for r in rows if r["naturalness"]]
    if nats:
        print(f"avg naturalness: {sum(nats)/len(nats):.1f}/5  (ADR-022; 5=native, 1=textbook)\n")
    for lvl in levels:
        sub = [r for r in rows if r["target"] == lvl]
        c = {"above": 0, "on": 0, "below": 0}
        for r in sub:
            c[r["class"]] += 1
        print(f"  {lvl}: on {c['on']}/{len(sub)} · ↑{c['above']} · ↓{c['below']}")
    print("\nThe judge is an LLM, not ground truth — read as a drift/richness signal "
          "and generator comparison, not a certified CEFR grade.")

    out_dir = os.path.join(os.path.dirname(__file__), "results")
    os.makedirs(out_dir, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    path = os.path.join(out_dir, f"story_level_{stamp}.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump({"generator": args.gen, "judge": args.judge, "sentences": args.sentences,
                   "summary": records, "stories": rows}, f, ensure_ascii=False, indent=2)
    print(f"\nFull stories + judgments: {path}")


if __name__ == "__main__":
    main()
