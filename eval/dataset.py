"""Gold dataset of German learner sentences with known errors.

Each case is a real learner-style sentence paired with:
  - the canonical corrected form (== text when the sentence is already correct)
  - the set of error categories present (empty when correct)

Design notes
------------
* Roughly half the cases are ALREADY CORRECT. This is deliberate: the hardest
  and most important thing for a teaching app is to NOT invent errors in good
  sentences. A model that "helpfully" rewrites correct German destroys trust.
  The correct cases drive the false-positive metric, which is the headline
  number for whether the core idea is viable.
* Error cases cover the common CEFR A1-B2 learner error families.
* `corrected` is the minimal fix preserving the learner's intent, so we can
  score the model's correction against a single canonical target.
"""

from dataclasses import dataclass, field

from taxonomy import ErrorCategory as E


@dataclass(frozen=True)
class Case:
    id: str
    level: str            # A1 / A2 / B1 / B2
    text: str             # the learner sentence
    corrected: str        # canonical correct version (== text if already correct)
    errors: tuple = field(default_factory=tuple)  # tuple[ErrorCategory, ...]

    @property
    def is_correct(self) -> bool:
        return len(self.errors) == 0


CASES = [
    # ---- A1 ----
    Case("a01", "A1", "Ich habe einen Hund.", "Ich habe einen Hund."),
    Case("a02", "A1", "Ich heiße Anna und komme aus Spanien.",
         "Ich heiße Anna und komme aus Spanien."),
    Case("a03", "A1", "Er trinken Wasser.", "Er trinkt Wasser.",
         (E.VERB_CONJUGATION,)),
    Case("a04", "A1", "Das ist eine Tisch.", "Das ist ein Tisch.",
         (E.GENDER,)),
    Case("a05", "A1", "Ich sehe der Mann.", "Ich sehe den Mann.",
         (E.CASE,)),
    Case("a06", "A1", "ich wohne in berlin.", "Ich wohne in Berlin.",
         (E.SPELLING,)),
    Case("a07", "A1", "Wir spielen am Samstag Fußball.",
         "Wir spielen am Samstag Fußball."),

    # ---- A2 ----
    Case("a08", "A2", "Ich habe gestern nach Hause gegangen.",
         "Ich bin gestern nach Hause gegangen.", (E.AUX_CHOICE,)),
    Case("a09", "A2", "Sie hat ein Buch gelest.", "Sie hat ein Buch gelesen.",
         (E.VERB_CONJUGATION,)),
    Case("a10", "A2", "Ich rufe an meine Mutter jeden Tag.",
         "Ich rufe meine Mutter jeden Tag an.", (E.SEPARABLE_VERB,)),
    Case("a11", "A2", "Wir fahren mit dem Auto zur Arbeit.",
         "Wir fahren mit dem Auto zur Arbeit."),
    Case("a12", "A2", "Ich gebe der Frau das Buch.",
         "Ich gebe der Frau das Buch."),
    Case("a13", "A2", "Ich helfe meinen Bruder.", "Ich helfe meinem Bruder.",
         (E.CASE,)),
    Case("a14", "A2", "Er ist größer als ich.", "Er ist größer als ich."),

    # ---- B1 ----
    Case("b01", "B1", "Ich weiß, dass er kommt morgen.",
         "Ich weiß, dass er morgen kommt.", (E.VERB_POSITION,)),
    Case("b02", "B1", "Weil ich bin müde, gehe ich ins Bett.",
         "Weil ich müde bin, gehe ich ins Bett.", (E.VERB_POSITION,)),
    Case("b03", "B1", "Ich habe ein schönes Auto gekauft.",
         "Ich habe ein schönes Auto gekauft."),
    Case("b04", "B1", "Ich interessiere mich für Politik.",
         "Ich interessiere mich für Politik."),
    Case("b05", "B1", "Ich warte auf dem Bus.", "Ich warte auf den Bus.",
         (E.PREPOSITION,)),
    Case("b06", "B1", "Mit ein guter Freund gehe ich ins Kino.",
         "Mit einem guten Freund gehe ich ins Kino.",
         (E.CASE, E.ADJ_ENDING)),
    Case("b07", "B1", "Das ist das Auto von mein Vater.",
         "Das ist das Auto von meinem Vater.", (E.CASE,)),
    Case("b08", "B1", "Ich habe keine Zeit.", "Ich habe keine Zeit."),

    # ---- B2 ----
    Case("b09", "B2", "Wenn ich Zeit hätte, würde ich dich besuchen.",
         "Wenn ich Zeit hätte, würde ich dich besuchen."),
    Case("b10", "B2", "Der Mann, den ich gestern gesehen habe, ist mein Lehrer.",
         "Der Mann, den ich gestern gesehen habe, ist mein Lehrer."),
    Case("b11", "B2", "Obwohl es regnet, wir gehen spazieren.",
         "Obwohl es regnet, gehen wir spazieren.", (E.VERB_POSITION,)),
    Case("b12", "B2", "Ich freue mich auf das Wochenende.",
         "Ich freue mich auf das Wochenende."),

    # ---- C1 ----
    # correct: Konjunktiv I in reported speech (must NOT be "corrected")
    Case("c01", "C1", "Der Sprecher betonte, die Regierung werde die Steuern nicht erhöhen.",
         "Der Sprecher betonte, die Regierung werde die Steuern nicht erhöhen."),
    # correct: extended participial attribute + passive
    Case("c02", "C1", "Die von der Kommission vorgeschlagenen Maßnahmen wurden abgelehnt.",
         "Die von der Kommission vorgeschlagenen Maßnahmen wurden abgelehnt."),
    # correct: trotz + Genitiv, separable verb
    Case("c03", "C1", "Trotz des schlechten Wetters fand die Veranstaltung im Freien statt.",
         "Trotz des schlechten Wetters fand die Veranstaltung im Freien statt."),
    # error: Vorgangspassiv Perfekt uses "worden", not "geworden"
    Case("c04", "C1", "Das Museum ist im 19. Jahrhundert gebaut geworden.",
         "Das Museum ist im 19. Jahrhundert gebaut worden.", (E.PASSIVE,)),
    # error: relative pronoun case — treffen + Akkusativ -> "den", not "dem"
    Case("c05", "C1", "Das ist der Kollege, dem ich gestern auf der Konferenz getroffen habe.",
         "Das ist der Kollege, den ich gestern auf der Konferenz getroffen habe.",
         (E.RELATIVE_CLAUSE,)),
    # error: je…desto word order in the second clause
    Case("c06", "C1", "Je mehr Geld er verdient, desto er gibt mehr aus.",
         "Je mehr Geld er verdient, desto mehr gibt er aus.", (E.CONNECTOR,)),

    # ---- C2 ----
    # correct: formal register, angesichts + Genitiv, sich gezwungen sehen
    Case("c07", "C2", "Angesichts der angespannten Lage sah sich die Regierung gezwungen, sofort zu handeln.",
         "Angesichts der angespannten Lage sah sich die Regierung gezwungen, sofort zu handeln."),
    # correct: modal particles (doch, einfach, mal) — idiomatic, NOT errors
    Case("c08", "C2", "Komm doch einfach mal bei uns vorbei, wenn du Zeit hast.",
         "Komm doch einfach mal bei uns vorbei, wenn du Zeit hast."),
    # correct: gerundive participial attribute (zu + Partizip I)
    Case("c09", "C2", "Es handelt sich um ein nicht zu unterschätzendes Risiko.",
         "Es handelt sich um ein nicht zu unterschätzendes Risiko."),
    # error: participial attribute needs the plural ending -> "erwähnten"
    Case("c10", "C2", "Die in dem Bericht erwähnte Zahlen sind längst veraltet.",
         "Die in dem Bericht erwähnten Zahlen sind längst veraltet.", (E.PARTICIPIAL,)),
    # error: irrealis past — "wäre … gekommen", not "würde … gekommen sein"
    Case("c11", "C2", "Wenn ich das gewusst hätte, würde ich nicht gekommen sein.",
         "Wenn ich das gewusst hätte, wäre ich nicht gekommen.", (E.SUBJUNCTIVE_II,)),
    # error: relative pronoun gender — feminine antecedent -> "deren", not "dessen"
    Case("c12", "C2", "Ich kenne eine Frau, dessen Mann Arzt ist.",
         "Ich kenne eine Frau, deren Mann Arzt ist.", (E.RELATIVE_CLAUSE,)),
]


def summary():
    n = len(CASES)
    n_correct = sum(c.is_correct for c in CASES)
    return n, n_correct, n - n_correct
