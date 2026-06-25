"""Deterministic stand-in for the real tutor.

Used by `run_eval.py --mock` so the harness can be exercised end-to-end with no
API key. It returns the gold answer for most cases but injects controlled
mistakes for a few specific ids, so every scoring path (missed error, invented
error, wrong category, wrong correction) is exercised and the report shows
non-trivial numbers. This verifies the harness MECHANICS, not Claude's quality.
"""

from dataset import CASES
from tutor import DetectedError, TutorFeedback

_BY_ID = {c.id: c for c in CASES}

# Controlled noise to make the metrics move:
_MISS_DETECTION = {"a09"}          # has an error but mock reports none (false negative)
_INVENT_ON_CORRECT = {"a11", "b04"}  # correct sentences the mock wrongly "fixes"
_WRONG_CATEGORY = {"b06": "VERB_CONJUGATION"}  # right that it's wrong, wrong label
_WRONG_CORRECTION = {"b01"}        # detects + categorises, but botches the rewrite
# Mock an over-claim of an advanced skill on a simple correct sentence, so the
# demonstrated-skills eval has a non-zero over-claim to catch (mirrors how the
# other injections exercise the grammar metrics).
_OVERCLAIM_DEMONSTRATED = {"a01": "PASSIVE"}


def _gold_feedback(case) -> TutorFeedback:
    from taxonomy import ErrorCategory
    errs = [
        DetectedError(category=cat, original_fragment="…", correction="…",
                      explanation="(gold)")
        for cat in case.errors
    ]
    # Plausible demonstrated skills: for a correct sentence, "show" one of its
    # level skills; for the injected case, deliberately over-claim an advanced one.
    demonstrated = []
    if case.id in _OVERCLAIM_DEMONSTRATED:
        demonstrated = [ErrorCategory(_OVERCLAIM_DEMONSTRATED[case.id])]
    elif not case.errors:
        demonstrated = []  # conservative default; the real model fills this in
    return TutorFeedback(has_errors=bool(case.errors),
                         corrected_sentence=case.corrected, errors=errs,
                         demonstrated=demonstrated)


def get_feedback(_client, level: str, sentence: str) -> TutorFeedback:
    case = next((c for c in CASES if c.text == sentence), None)
    if case is None:
        return TutorFeedback(has_errors=False, corrected_sentence=sentence, errors=[])

    if case.id in _MISS_DETECTION:
        return TutorFeedback(has_errors=False, corrected_sentence=sentence, errors=[])

    if case.id in _INVENT_ON_CORRECT:
        from taxonomy import ErrorCategory
        return TutorFeedback(
            has_errors=True,
            corrected_sentence=sentence + " wirklich",
            errors=[DetectedError(category=ErrorCategory.WORD_ORDER,
                                  original_fragment="…", correction="…",
                                  explanation="(invented)")],
        )

    fb = _gold_feedback(case)

    if case.id in _WRONG_CATEGORY:
        from taxonomy import ErrorCategory
        bad = ErrorCategory(_WRONG_CATEGORY[case.id])
        fb = TutorFeedback(
            has_errors=True, corrected_sentence=case.corrected,
            errors=[DetectedError(category=bad, original_fragment="…",
                                  correction="…", explanation="(wrong label)")],
        )

    if case.id in _WRONG_CORRECTION:
        fb = TutorFeedback(has_errors=True,
                           corrected_sentence="völlig falsche Korrektur",
                           errors=fb.errors)

    return fb
