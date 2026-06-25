"""Shared error taxonomy for the German-grammar feedback eval.

One closed set of categories used in three places:
  - the gold dataset annotations (dataset.py)
  - the structured-output schema the tutor must return (tutor.py)
  - the scorer that compares them (score.py)

Keeping it in one place means the model can only ever return a label we
actually score against, and the scorer never sees a surprise category.
"""

from enum import Enum


class ErrorCategory(str, Enum):
    CASE = "CASE"                      # wrong case: Nom/Akk/Dat/Gen (incl. verb/prep government)
    GENDER = "GENDER"                  # wrong article/pronoun gender (der/die/das, ein/eine)
    ADJ_ENDING = "ADJ_ENDING"         # wrong adjective declension ending
    VERB_CONJUGATION = "VERB_CONJUGATION"  # agreement or wrong finite/participle form
    VERB_POSITION = "VERB_POSITION"   # V2 / verb-final in subordinate clauses / inversion
    AUX_CHOICE = "AUX_CHOICE"         # sein vs haben in the perfect
    SEPARABLE_VERB = "SEPARABLE_VERB" # misplaced separable prefix
    PREPOSITION = "PREPOSITION"       # wrong preposition or preposition+case pairing
    WORD_ORDER = "WORD_ORDER"         # general ordering (TeKaMoLo etc.) not covered above
    PLURAL = "PLURAL"                 # wrong plural form
    NEGATION = "NEGATION"             # nicht vs kein, negation placement
    SPELLING = "SPELLING"             # spelling / noun capitalisation
    # --- advanced grammar (B1+ / C1 / C2) ---
    RELATIVE_CLAUSE = "RELATIVE_CLAUSE"   # wrong relative pronoun (case/gender/number) or structure
    CONNECTOR = "CONNECTOR"               # wrong connector or the word order it triggers
    SUBJUNCTIVE_II = "SUBJUNCTIVE_II"     # Konjunktiv II: hypothetical / polite / unreal (würde, hätte, wäre)
    SUBJUNCTIVE_I = "SUBJUNCTIVE_I"       # Konjunktiv I: indirect / reported speech
    PASSIVE = "PASSIVE"                   # Passiv formed wrongly (werden/sein + Partizip II, agent)
    NOMINALIZATION = "NOMINALIZATION"     # Nominalstil: nominalisation / verbal-vs-nominal style mismatch
    PARTICIPIAL = "PARTICIPIAL"           # extended participial attribute (Partizip I/II as pre-nominal attribute)
    MODAL_PARTICLE = "MODAL_PARTICLE"     # misused/misplaced modal particle (doch, mal, eben, halt, ja)


# Human-readable hints injected into the tutor prompt so the model knows
# exactly what each label means and doesn't invent its own taxonomy.
CATEGORY_HINTS = {
    ErrorCategory.CASE: "Wrong grammatical case, including case required by a verb (helfen+Dativ) or preposition.",
    ErrorCategory.GENDER: "Wrong gender on an article or pronoun (der/die/das, ein/eine/ein).",
    ErrorCategory.ADJ_ENDING: "Wrong adjective declension ending.",
    ErrorCategory.VERB_CONJUGATION: "Subject-verb agreement error or wrong verb form (incl. wrong past participle).",
    ErrorCategory.VERB_POSITION: "Finite verb in the wrong slot: V2 violated, not verb-final in a subordinate clause, or missing inversion.",
    ErrorCategory.AUX_CHOICE: "Wrong perfect-tense auxiliary (sein vs haben).",
    ErrorCategory.SEPARABLE_VERB: "Separable prefix in the wrong position.",
    ErrorCategory.PREPOSITION: "Wrong preposition, or correct preposition with the wrong case.",
    ErrorCategory.WORD_ORDER: "Constituent order wrong in a way not captured by VERB_POSITION.",
    ErrorCategory.PLURAL: "Wrong plural form of a noun.",
    ErrorCategory.NEGATION: "Wrong negation: nicht vs kein, or negation in the wrong place.",
    ErrorCategory.SPELLING: "Spelling mistake or a noun not capitalised.",
    ErrorCategory.RELATIVE_CLAUSE: "Relative clause: wrong relative pronoun (case/gender/number) or structure.",
    ErrorCategory.CONNECTOR: "Wrong connector/conjunction or the word order it triggers (deshalb, trotzdem, je…desto, weder…noch).",
    ErrorCategory.SUBJUNCTIVE_II: "Konjunktiv II error: hypothetical, polite, or unreal forms (würde+Inf, hätte, wäre, könnte).",
    ErrorCategory.SUBJUNCTIVE_I: "Konjunktiv I error: indirect/reported speech (er sagte, er sei/habe/komme).",
    ErrorCategory.PASSIVE: "Passive voice formed incorrectly (werden/sein + Partizip II, wrong auxiliary, agent with von/durch).",
    ErrorCategory.NOMINALIZATION: "Nominal-style error: faulty nominalisation or verbal/nominal style mismatch in formal register.",
    ErrorCategory.PARTICIPIAL: "Extended participial attribute formed incorrectly (Partizip I/II used as a pre-nominal attribute).",
    ErrorCategory.MODAL_PARTICLE: "Modal particle misused or misplaced (doch, mal, eben, halt, ja, schon).",
}


def taxonomy_prompt_block() -> str:
    """Render the taxonomy as a bulleted block for the system prompt."""
    return "\n".join(f"- {c.value}: {CATEGORY_HINTS[c]}" for c in ErrorCategory)
