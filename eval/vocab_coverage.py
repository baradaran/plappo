"""Deterministic lexical-coverage check (ADR-019).

Given a German text and a target CEFR level, compute what fraction of its content
words fall within that level's vocabulary band, counting glossed words as supported
(the i+1 budget). No LLM call — fast, free, repeatable. The *measurable* half of the
story gate, complementing the LLM judge; also exposes the learner's *content*
vocabulary for the measured-level axis (ADR-009).

Built on real data, not a bootstrap:
  - lemmatisation via `simplemma` (handles irregulars: fuhr→fahren, teuren→teuer)
  - frequency via `wordfreq` Zipf scale (der≈7.5, haus≈5.4, sandburg≈2.2)
A lemma is "within level L" if its Zipf frequency ≥ the band threshold. This is
lexical-frequency profiling (Laufer & Nation 1995). Frequency is a principled but
imperfect proxy for CEFR — so the gate threshold stays lenient (catch *gross* drift;
the judge handles nuance). Thresholds are the one tunable; everything else is data.
"""

import re

from simplemma import lemmatize
from wordfreq import zipf_frequency

# Zipf threshold a lemma must clear to count as "within" each level (cumulative:
# higher level → lower bar → more words allowed). Calibrated so everyday words pass
# at A1–A2 while low-frequency/technical words (Industrialisierung, Sandburg) fall
# out. Tune here if the gate is too strict/loose.
ZIPF_BANDS = {"A1": 4.0, "A2": 3.6, "B1": 3.2, "B2": 2.8, "C1": 2.4, "C2": 2.0}
_ORDER = ["A1", "A2", "B1", "B2", "C1", "C2"]
COVERAGE_THRESHOLD = 0.85

# Small closed-class stoplist so classify_vocab() reports *content* words only.
# (Coverage doesn't need it — function words have very high Zipf and pass anyway.)
_STOP = set("""
der die das den dem des ein eine einen einem einer eines kein keine
ich du er sie es wir ihr man mich dich sich uns euch mir dir ihm ihnen
mein dein sein unser euer dieser diese dieses jener welche welcher alle jeder
in an auf über unter vor hinter neben zwischen mit ohne für gegen um durch bei
nach zu von aus seit bis trotz während wegen im am beim zum zur ins ans vom
und oder aber denn weil dass wenn als ob obwohl damit sondern sowie weder noch
nicht auch nur noch schon dann da dort hier so sehr mehr ganz immer wieder ja nein doch mal
sein haben werden können müssen wollen sollen dürfen mögen
""".split())

_lemma_cache = {}


def _lemma(w):
    v = _lemma_cache.get(w)
    if v is None:
        v = lemmatize(w, lang="de")
        _lemma_cache[w] = v
    return v


def _zipf(lemma, surface):
    # lemma frequency is more stable, but fall back to the surface form.
    return max(zipf_frequency(lemma, "de"), zipf_frequency(surface, "de"))


def band_of(lemma, surface=None):
    """Lowest CEFR level whose threshold this lemma clears, or None (beyond C2)."""
    z = _zipf(lemma, surface or lemma)
    for lvl in _ORDER:
        if z >= ZIPF_BANDS[lvl]:
            return lvl
    return None


def coverage(text, level, gloss_forms=()):
    """Return {coverage, total, covered, uncovered[], in_band}."""
    threshold = ZIPF_BANDS.get(level, ZIPF_BANDS["C2"])
    gloss = {g.lower() for g in gloss_forms}
    gloss_lem = {_lemma(g) for g in gloss}

    tokens = re.findall(r"[a-zA-ZäöüÄÖÜß]+", text.lower())
    if not tokens:
        return {"coverage": 1.0, "total": 0, "covered": 0, "uncovered": [], "in_band": True}

    uncovered, covered = [], 0
    for t in tokens:
        lem = _lemma(t)
        if _zipf(lem, t) >= threshold or t in gloss or lem in gloss_lem:
            covered += 1
        else:
            uncovered.append(t)
    cov = covered / len(tokens)
    seen, uniq = set(), []
    for w in uncovered:
        if w not in seen:
            seen.add(w)
            uniq.append(w)
    return {"coverage": round(cov, 3), "total": len(tokens), "covered": covered,
            "uncovered": uniq, "in_band": cov >= COVERAGE_THRESHOLD}


def classify_vocab(text):
    """The *content* vocabulary a learner produced in `text`: distinct content
    lemmas, each tagged with the lowest CEFR band it falls in (None if beyond C2).
    Deterministic and LLM-free; used to measure the vocabulary axis from content
    words so function words and verbosity don't inflate it (ADR-009)."""
    out = {}
    for t in re.findall(r"[a-zA-ZäöüÄÖÜß]+", text.lower()):
        if len(t) <= 1:
            continue
        lem = _lemma(t)
        if lem in _STOP or t in _STOP or lem in out:
            continue
        out[lem] = {"lemma": lem, "surface": t, "band": band_of(lem, t)}
    return list(out.values())


if __name__ == "__main__":
    import sys
    lvl = sys.argv[1] if len(sys.argv) > 1 else "A2"
    txt = sys.argv[2] if len(sys.argv) > 2 else "Die Industrialisierung beschleunigte den Wandel."
    print(coverage(txt, lvl))
