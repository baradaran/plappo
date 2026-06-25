"""Deterministic lexical-coverage check (ADR-019).

Given a German text and a target CEFR level, compute what fraction of its words
fall within that level's vocabulary band (data/vocab_bands.json), counting glossed
words as supported (the i+1 budget). No LLM call — fast, free, repeatable. This is
the *measurable* half of the story gate, complementing the LLM judge.

Quality is bounded by the band list (a bootstrap approximation — see
build_vocab_bands.py) and by a heuristic stemmer that approximates German
inflection without a morphology library. Both are swappable without changing the
interface. Threshold is deliberately lenient for now; with a real Goethe/corpus
list + a proper lemmatiser you'd raise it toward the ~98% comprehension figure
(Hu & Nation 2000).
"""

import json
import os
import re

_BANDS_PATH = os.path.join(os.path.dirname(__file__), "data", "vocab_bands.json")
# Deliberately lenient: the band list + heuristic stemmer are an approximation, so
# this gate's job is to catch *gross* out-of-band drift (e.g. "Industrialisierung"
# in an A2 story) cheaply, while the LLM judge handles the nuance. Raise toward the
# ~0.98 comprehension figure once a real Goethe/corpus list + lemmatiser are in.
COVERAGE_THRESHOLD = 0.80

# Closed-class function words + the most common irregular/contracted forms. These
# are A1 by definition and the band-list+stemmer can't reach them (der≠article
# lemma, war≠sein, zur=contraction). Without this the gate flags the commonest
# German words. Finite and high-value; this is the bulk of the fix.
_FUNCTION_WORDS = set("""
der die das den dem des ein eine einen einem einer eines kein keine keinen keinem keiner
ich du er sie es wir ihr man mich dich sich uns euch mir dir ihm ihnen
mein meine meinen meinem meiner dein deine sein seine seinen seinem ihre ihren ihrem unser unsere euer
dieser diese dieses diesen diesem jener jene welche welcher welches alle alles jeder jede jedes
in an auf über unter vor hinter neben zwischen mit ohne für gegen um durch bei nach zu von aus seit bis
trotz während wegen statt gegenüber innerhalb außerhalb entlang
im am beim zum zur ins ans aufs vom fürs durchs ums
und oder aber denn weil dass daß wenn als ob obwohl damit sondern sowie sowohl weder noch
nicht auch nur noch schon dann da dort hier so sehr mehr ganz immer wieder ja nein doch mal eben halt
hin her heraus hinein zurück
bin bist ist sind seid war warst waren gewesen sei
habe hast hat haben hatte hattest hatten gehabt
werde wirst wird werden wurde wurden geworden worden
kann kannst können konnte konnten muss musst müssen musste mussten
will willst wollen wollte wollten soll sollst sollen sollte sollten darf dürfen mag möchte möchten
geht ging gehen kommt kam kommen sah sehen gab geben fand finden
sehr viel viele wenig etwas nichts alles jemand niemand
am am
""".split())

# Longest suffixes first; crude German inflection stripping.
_SUFFIXES = ["lichen", "ischen", "ische", "ungen", "keit", "heit", "lich", "isch",
             "bar", "ung", "ern", "est", "end", "en", "em", "er", "es", "st",
             "et", "te", "e", "n", "s", "t"]


def _stem(w):
    # iterate so multi-suffix inflections reduce consistently:
    # spielten -> spiel, spielen -> spiel (the band and the token must agree)
    prev = None
    while w != prev and len(w) > 3:
        prev = w
        for s in _SUFFIXES:
            if w.endswith(s) and len(w) - len(s) >= 3:
                w = w[: -len(s)]
                break
    return w


_bands = None
_stemmed = None


def _load():
    global _bands, _stemmed
    if _bands is None:
        try:
            with open(_BANDS_PATH, encoding="utf-8") as f:
                _bands = json.load(f)
        except (OSError, json.JSONDecodeError):
            _bands = {}
        _stemmed = {lvl: {_stem(w) for w in words} for lvl, words in _bands.items()}
    return _bands, _stemmed


def coverage(text, level, gloss_forms=()):
    """Return {coverage, total, covered, uncovered[], in_band}."""
    bands, stemmed = _load()
    allowed = set(bands.get(level, []))
    allowed_st = stemmed.get(level, set())
    gloss = {g.lower() for g in gloss_forms}
    gloss_st = {_stem(g) for g in gloss}

    tokens = re.findall(r"[a-zäöüß]+", text.lower())
    if not tokens:
        return {"coverage": 1.0, "total": 0, "covered": 0, "uncovered": [], "in_band": True}

    uncovered, covered = [], 0
    for t in tokens:
        st = _stem(t)
        if (t in _FUNCTION_WORDS or t in allowed or st in allowed_st
                or t in gloss or st in gloss_st):
            covered += 1
        else:
            uncovered.append(t)
    cov = covered / len(tokens)
    # de-dup uncovered, preserve order
    seen, uniq = set(), []
    for w in uncovered:
        if w not in seen:
            seen.add(w)
            uniq.append(w)
    return {"coverage": round(cov, 3), "total": len(tokens), "covered": covered,
            "uncovered": uniq, "in_band": cov >= COVERAGE_THRESHOLD}


if __name__ == "__main__":  # quick manual check
    import sys
    lvl = sys.argv[1] if len(sys.argv) > 1 else "A2"
    txt = sys.argv[2] if len(sys.argv) > 2 else "Das Museum wurde im 19. Jahrhundert gebaut."
    print(coverage(txt, lvl))
