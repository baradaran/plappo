"""The grammar-feedback engine under test.

This is the component the whole app hinges on: given a learner sentence and its
CEFR level, return structured, reliable grammar feedback. We use Claude with
*structured outputs* (a JSON schema enforced by the API) so the harness always
gets a parseable result with categories drawn only from our taxonomy.

Model: claude-opus-4-8 by default (override with GERMAN_TUTOR_MODEL). Opus is the
right default for the eval — we want to know the ceiling of feedback quality
before deciding what to ship in production.
"""

import os
from typing import List

from pydantic import BaseModel, Field

from taxonomy import ErrorCategory, taxonomy_prompt_block

MODEL = os.environ.get("GERMAN_TUTOR_MODEL", "claude-opus-4-8")


# ---- Structured output schema -------------------------------------------------
# The model is constrained to this shape. `category` can only be a taxonomy enum
# value, so the scorer never receives an unknown label.

class DetectedError(BaseModel):
    category: ErrorCategory = Field(description="Single best-fitting category for this error.")
    original_fragment: str = Field(description="The exact incorrect span from the learner's sentence.")
    correction: str = Field(description="What that span should be.")
    explanation: str = Field(description="One short sentence, learner-friendly, explaining the rule.")


class TutorFeedback(BaseModel):
    has_errors: bool = Field(description="True if the sentence contains at least one grammatical error.")
    corrected_sentence: str = Field(description="The full corrected sentence. If already correct, repeat it unchanged.")
    errors: List[DetectedError] = Field(description="One entry per grammatical error. Empty if none.")


SYSTEM_PROMPT = f"""You are a precise German grammar tutor for a CEFR learner.

You are given one sentence written by a learner, plus their level (A1-B2).
Identify ONLY genuine grammatical errors. Follow these rules strictly:

1. If the sentence is grammatically correct, set has_errors=false, return the
   sentence unchanged in corrected_sentence, and return an empty errors list.
   Do NOT rewrite correct German for style, naturalness, or preference.
2. Flag only grammar mistakes (case, gender, agreement, word order, etc.) — not
   stylistic choices, register, or alternative valid phrasings.
3. Classify each error with exactly one label from this closed taxonomy:
{taxonomy_prompt_block()}
4. corrected_sentence must be the MINIMAL fix that makes the sentence
   grammatical while preserving the learner's intended meaning. Keep their words
   and content where possible.
5. Keep each explanation to one short, encouraging sentence a learner can act on.
"""


def build_client():
    import anthropic
    return anthropic.Anthropic()


def get_feedback(client, level: str, sentence: str) -> TutorFeedback:
    """Run one sentence through the tutor and return parsed feedback."""
    resp = client.messages.parse(
        model=MODEL,
        max_tokens=2000,
        system=SYSTEM_PROMPT,
        messages=[{
            "role": "user",
            "content": f"Learner level: {level}\nSentence: {sentence}",
        }],
        output_format=TutorFeedback,
    )
    if resp.parsed_output is None:
        # Refusal or schema miss — treat as "no usable feedback".
        return TutorFeedback(has_errors=False, corrected_sentence=sentence, errors=[])
    return resp.parsed_output
