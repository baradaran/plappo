# Privacy & data — how Plappo handles your data (GDPR / BDSG / TDDDG)

This describes how the app collects and uses data, designed around EU/German law
(GDPR/DSGVO, the German BDSG, and TDDDG §25 for client-side storage).

> **Not legal advice.** This is a good-faith *engineering* implementation of the
> GDPR principles. Before any public/production launch, have a data-protection
> lawyer or DPO review it, complete a Record of Processing (Art. 30), sign a
> processor agreement (Art. 28) with the LLM provider, and assess international
> transfer (Art. 44+). See "Before production" below.

## Two separate data flows

**1. Processing to provide the service (always on, inherent to using the app).**
When you ask for grammar feedback or open a story, your written German / the
request is sent to the **LLM provider (Google Vertex AI)** to produce the
response. This is necessary to deliver the feature you asked for
(*Art. 6(1)(b)* — performance of the service). The provider is a **processor**;
in production this needs a Data Processing Agreement and an international-transfer
assessment. **Implication:** don't type personal details into answers.

**2. Optional analytics logging (off until you opt in).** To improve the product
we can log your learning events. **Nothing is logged until you press "Allow."**

## What the analytics log contains (only after consent)

- The German sentences you write and the feedback result (error categories,
  correction, demonstrated skills).
- Review events: card category, your grade, and the spaced-repetition state
  change (stability/difficulty, elapsed days) — used to optimise the FSRS schedule.
- Story events: target level and the gate result (estimated level, lexical
  coverage, naturalness) — used to calibrate content generation.
- A **random pseudonymous id** so your events can be grouped (e.g. for per-user
  FSRS tuning).

## What it does **not** contain

- **No** name, email, or account. **No** IP address (the server never stores it).
  **No** device fingerprint. **No** precise location. **No** advertising IDs.
- Timestamps are coarsened to the **day**, not the second.

## Legal basis

- Analytics logging: your **consent** (*Art. 6(1)(a) GDPR*), and **TDDDG §25**
  consent for storing/reading data on your device. Opt-in, never pre-ticked,
  withdrawable at any time.
- A pseudonymous id is still *personal data* under the GDPR, which is exactly why
  it sits behind consent and the rights below.

## Purposes (purpose limitation)

Improve the grammar-feedback engine, optimise spaced-repetition scheduling, and
calibrate level/content generation. **No** advertising, **no** sale of data, **no**
automated decisions with legal/significant effects, **no** profiling beyond
improving your own learning.

## Your rights — and where to use them

| Right (GDPR) | In the app |
|---|---|
| Withdraw consent (Art. 7(3)) | Profile → Data & privacy → **Turn off** |
| Access + portability (Art. 15/20) | Profile → **Export my data** (downloads JSON) |
| Erasure (Art. 17) | Profile → **Delete my data** |
| Object / restrict (Art. 18/21) | Turn off + delete |

## Data minimisation & retention

We log only what serves the stated purposes. Data is kept until you delete it or
withdraw consent. *(Production: set a concrete maximum retention and auto-expiry.)*

## Children

Under the GDPR (Art. 8) Germany sets the digital-consent age at **16**. A
production deployment aimed at or reachable by minors needs age assurance and
parental consent. *(Not implemented in this prototype.)*

## Where data lives (prototype)

Analytics events are written to a local file on the server
(`prototype/data/events.jsonl`, git-ignored). No third-party analytics. The only
external processor is the LLM provider (flow #1 above).

## Before production (engineering TODO, not yet done)

- DPA (Art. 28) with the LLM provider; document the international transfer (Art.
  44+) and run a Transfer Impact Assessment if data leaves the EU; prefer an
  EU region.
- Record of Processing Activities (Art. 30); a DPIA if scale/risk warrants.
- A real consent-management record (versioned, timestamped — partially done) and
  a public privacy notice + imprint (Impressum, §5 DDG).
- Free-text PII handling: detect/redact obvious personal data in submitted
  sentences, and/or store the structured result only.
- Define retention limits + automatic deletion; encrypt at rest; access controls.
- Age assurance / parental consent if minors are in scope.
