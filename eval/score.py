"""Scoring: compare tutor predictions against the gold dataset.

We report four things, because "is the feedback good?" is not one number:

1. Error DETECTION (binary): when a sentence has an error, does the tutor say so?
   And — the metric that decides viability — how often does it invent an error
   in a CORRECT sentence (false-positive rate)?

2. CATEGORY accuracy: of the errors it flags, are they the right *kind*?
   Micro precision/recall/F1 over the taxonomy.

3. CORRECTION accuracy: does its corrected_sentence match the canonical fix?
   Strict (punctuation-insensitive) string match — a hard but objective signal.

4. Per-LEVEL breakdown, so you can see if it falls apart at B1/B2.
"""

import re
from dataclasses import dataclass


def _norm(s: str) -> str:
    """Normalise for correction comparison: drop punctuation, collapse spaces.
    Case IS preserved — German capitalisation is meaningful."""
    s = re.sub(r"[.,!?;:\"']", " ", s)
    return re.sub(r"\s+", " ", s).strip()


@dataclass
class CaseResult:
    case_id: str
    level: str
    is_correct: bool          # gold: was the sentence already correct?
    gold_cats: frozenset
    pred_cats: frozenset
    pred_has_errors: bool     # did the model flag anything?
    correction_ok: bool       # did corrected_sentence match canonical?

    # per-case category confusion
    @property
    def tp(self): return len(self.gold_cats & self.pred_cats)
    @property
    def fp(self): return len(self.pred_cats - self.gold_cats)
    @property
    def fn(self): return len(self.gold_cats - self.pred_cats)


def score_case(case, feedback) -> CaseResult:
    gold_cats = frozenset(case.errors)
    pred_cats = frozenset(e.category for e in feedback.errors)
    pred_has_errors = feedback.has_errors or len(feedback.errors) > 0
    correction_ok = _norm(feedback.corrected_sentence) == _norm(case.corrected)
    return CaseResult(
        case_id=case.id, level=case.level, is_correct=case.is_correct,
        gold_cats=gold_cats, pred_cats=pred_cats,
        pred_has_errors=pred_has_errors, correction_ok=correction_ok,
    )


def _prf(tp, fp, fn):
    p = tp / (tp + fp) if (tp + fp) else 0.0
    r = tp / (tp + fn) if (tp + fn) else 0.0
    f = 2 * p * r / (p + r) if (p + r) else 0.0
    return p, r, f


def aggregate(results):
    n = len(results)
    correct = [r for r in results if r.is_correct]
    errored = [r for r in results if not r.is_correct]

    # --- binary detection (does a sentence contain an error?) ---
    det_tp = sum(1 for r in errored if r.pred_has_errors)         # error caught
    det_fn = sum(1 for r in errored if not r.pred_has_errors)     # error missed
    det_fp = sum(1 for r in correct if r.pred_has_errors)         # invented error
    det_p, det_r, det_f = _prf(det_tp, det_fp, det_fn)
    false_positive_rate = det_fp / len(correct) if correct else 0.0
    clean_pass = sum(1 for r in correct if not r.pred_has_errors and r.correction_ok)

    # --- category micro P/R/F1 over all cases ---
    c_tp = sum(r.tp for r in results)
    c_fp = sum(r.fp for r in results)
    c_fn = sum(r.fn for r in results)
    cat_p, cat_r, cat_f = _prf(c_tp, c_fp, c_fn)

    # --- correction accuracy ---
    corr_err = sum(r.correction_ok for r in errored)
    corr_ok_correct = sum(r.correction_ok for r in correct)

    # --- per-level detection F1 ---
    levels = {}
    for lvl in sorted({r.level for r in results}):
        sub = [r for r in results if r.level == lvl]
        sub_err = [r for r in sub if not r.is_correct]
        sub_cor = [r for r in sub if r.is_correct]
        tp = sum(1 for r in sub_err if r.pred_has_errors)
        fn = sum(1 for r in sub_err if not r.pred_has_errors)
        fp = sum(1 for r in sub_cor if r.pred_has_errors)
        _, _, f = _prf(tp, fp, fn)
        levels[lvl] = {
            "n": len(sub), "detect_f1": round(f, 3),
            "false_positives": fp, "n_correct": len(sub_cor),
            "correction_acc": round(
                sum(r.correction_ok for r in sub_err) / len(sub_err), 3
            ) if sub_err else None,
        }

    return {
        "n_cases": n,
        "n_correct_sentences": len(correct),
        "n_error_sentences": len(errored),
        "detection": {
            "precision": round(det_p, 3), "recall": round(det_r, 3),
            "f1": round(det_f, 3),
            "errors_caught": det_tp, "errors_missed": det_fn,
            "false_positive_rate_on_correct": round(false_positive_rate, 3),
            "invented_errors": det_fp,
            "clean_pass_rate": round(clean_pass / len(correct), 3) if correct else None,
        },
        "category": {
            "precision": round(cat_p, 3), "recall": round(cat_r, 3),
            "f1": round(cat_f, 3), "tp": c_tp, "fp": c_fp, "fn": c_fn,
        },
        "correction": {
            "accuracy_on_error_sentences": round(corr_err / len(errored), 3) if errored else None,
            "unchanged_on_correct_sentences": round(corr_ok_correct / len(correct), 3) if correct else None,
        },
        "by_level": levels,
    }
