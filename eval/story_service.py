"""Gated story generation + a growing on-disk story library.

Generates a level-appropriate German story (with glossary + comprehension
questions), runs the in-level gate from story_level_eval, and — crucially —
TAGS every story (grammar points exercised, theme) and PERSISTS the in-band ones
to a shared library on disk. That makes today's on-demand generations a reusable
corpus: the scalable path is "generate once, select per user, add as you go"
(see docs/ARCHITECTURE.md → Story content), and this is the forward-compatible
data model for it. Selection-per-user is a later add, not a rewrite.

Pedagogical nuance (i+1): a few words *above* level are fine IF they're glossed —
supported new vocabulary is the "+1". The gate rejects a story only when it
drifts above level with over-level words that are NOT in its glossary.

In-app the judge defaults to Flash (fast/cheap); the offline eval uses Pro for
rigour. Returns the story plus a `check` block so the UI can show what passed.
"""

import json
import os
import random
import time

from taxonomy import ErrorCategory
from story_level_eval import classify, judge
from vertex_backend import vertex_json

THEMES = ["everyday", "family", "nature", "travel", "school",
          "animals", "food", "city", "friendship", "work"]

STORY_SCHEMA = {
    "type": "OBJECT",
    "properties": {
        "title": {"type": "STRING"},
        "sentences": {"type": "ARRAY", "items": {"type": "STRING"}},
        "glossary": {
            "type": "ARRAY",
            "items": {
                "type": "OBJECT",
                "properties": {
                    "word": {"type": "STRING"},     # surface form, as in the text
                    "lemma": {"type": "STRING"},
                    "pos": {"type": "STRING"},
                    "en": {"type": "STRING"},
                },
                "required": ["word", "lemma", "pos", "en"],
            },
        },
        "questions": {"type": "ARRAY", "items": {"type": "STRING"}},
        # --- tags for the library / future selection layer ---
        "grammar_points": {"type": "ARRAY",
                           "items": {"type": "STRING", "enum": [c.value for c in ErrorCategory]}},
        "theme": {"type": "STRING", "enum": THEMES},
    },
    "required": ["title", "sentences", "glossary", "questions", "grammar_points", "theme"],
}


def _gen_system(level):
    return (
        f"You write short stories in German for learners at exactly CEFR level {level}. "
        f"Use vocabulary and grammar appropriate to {level}; make it engaging and worth a "
        f"{level} learner's time, but do not exceed {level}.\n"
        f"Also return:\n"
        f"- glossary: the 5-8 key or hardest words a {level} learner might not know, each with "
        f"the surface form exactly as it appears in the text, its lemma, part of speech, and a "
        f"short English gloss.\n"
        f"- questions: 3 short comprehension questions in German at level {level}.\n"
        f"- grammar_points: which grammatical structures (from the allowed tag set) the story "
        f"actually exercises, so it can later be matched to a learner's weak points.\n"
        f"- theme: the closest theme tag."
    )


def _generate(model, level, topic, n, avoid):
    user = f"Write a {n}-sentence story at level {level}. Topic: {topic}."
    if avoid:
        user += f"\nDo NOT use these words (too hard): {', '.join(avoid)}. Use simpler ones."
    return vertex_json(model, _gen_system(level), user, STORY_SCHEMA, temperature=0.7)


def generate_gated_story(level, topic, gen_model="gemini-2.5-flash",
                         judge_model="gemini-2.5-flash", sentences=8, max_tries=2):
    avoid, story, check = [], {}, {}
    for attempt in range(1, max_tries + 1):
        story = _generate(gen_model, level, topic, sentences, avoid)
        text = " ".join(story.get("sentences", []))
        if not text:
            continue
        j = judge(judge_model, level, text)
        cls = classify(level, j)
        gloss_forms = set()
        for g in story.get("glossary", []):
            gloss_forms.add((g.get("word") or "").lower())
            gloss_forms.add((g.get("lemma") or "").lower())
        over = j.get("over_level_words", []) or []
        unsupported = [w for w in over if w.lower() not in gloss_forms]
        ship_ok = (cls != "above") or (not unsupported)
        check = {"target": level, "estimated": j.get("estimated_cefr"), "class": cls,
                 "over_words": over, "unsupported_over_words": unsupported,
                 "in_band": ship_ok, "attempts": attempt}
        if ship_ok:
            break
        avoid = unsupported  # regenerate, steering away from the leaked words
    story["check"] = check
    story["level"] = level
    story["topic"] = topic
    story["id"] = f"st_{level}_{int(time.time() * 1000)}"
    story["created_at"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    story["gen_model"] = gen_model
    story["source"] = "generated"
    return story


# --- the growing on-disk library ----------------------------------------------
_LIB_DIR = os.path.join(os.path.dirname(__file__), "library")
_LIB_PATH = os.path.join(_LIB_DIR, "stories.json")


def load_library():
    try:
        with open(_LIB_PATH, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, json.JSONDecodeError):
        return []


def save_to_library(story):
    """Append an in-band story to the shared corpus (no-op for drifted ones)."""
    if not story.get("check", {}).get("in_band"):
        return
    lib = load_library()
    lib.append(story)
    os.makedirs(_LIB_DIR, exist_ok=True)
    tmp = _LIB_PATH + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(lib, f, ensure_ascii=False, indent=2)
    os.replace(tmp, _LIB_PATH)


def select_from_library(level, exclude=()):
    """Cheap per-read selection from the corpus (no LLM call). The future
    personalised selector (match weak grammar_points / interests) slots in here."""
    cand = [s for s in load_library()
            if s.get("level") == level and s.get("id") not in exclude]
    return random.choice(cand) if cand else None
