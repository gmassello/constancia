# Deck

The content of the submitted slides, kept here so the claims stay next to the code that backs them.
Eleven slides. The market numbers come from [`INTENT.md`](INTENT.md) §3 and §4, with the citations;
everything about the system is checkable in this repo today.

---

## 1 · Title

# constancia

**An agent that phones your patients every week and remembers what they said last time.**

AssemblyAI Voice Agent Hackathon · September 2026

---

## 2 · The problem

**About 7 in 10 patients in home rehabilitation abandon their exercise plan.**

Not because the plan is wrong — because nobody follows up.

A physiotherapist with forty patients cannot make forty calls a week, so the follow-up simply does
not happen, and by the time the patient comes back in, the month is lost.

> The gap is not information. It is **attention that scales**.

---

## 3 · The product in one sentence

constancia places the call, asks the protocol questions in a fixed order, escalates the moment a red
flag shows up, writes a summary for the professional — and, the following week, **opens by asking
about what the patient said last time**.

That last part is the whole product.

---

## 4 · Week one → week two

**Week 1**
> — How much does it hurt today from one to ten?
> — My right knee hurts **seven out of ten**, especially when I climb stairs.

**Week 2, same patient, same questions**
> — Hi Ana, last week you told me your knee hurt seven out of ten climbing stairs, so I am calling
>   to see how it has been this week.
> — It is **four out of ten** now.

The 7/10 is not overwritten. It is **retired**: it stays in the file, struck through, with the dates
it was true for. The professional opens the panel and sees a chain, not a number.

---

## 5 · How it works

```
Twilio ──▶ FastAPI ──▶ orchestrator ──▶ Postgres + pgvector
             │              │
   AssemblyAI Universal-    ├── recall     the file becomes the prompt, and the
   Streaming v3 (µ-law      │              patient's own words become keyterms_prompt
   8 kHz, end-of-turn)      ├── converse   four questions, in declaration order
             │              ├── extract    facts, each anchored to a literal quote
   ElevenLabs Flash v2.5    ├── store      contradictions retire, nothing is deleted
   (ulaw_8000, barge-in)    └── summarize  one paragraph for the professional
```

**The code decides, the model phrases.** The question order, the red-flag guard and the supersession
are deterministic Python. The LLM writes sentences.

---

## 6 · Why the memory claim is checkable

1. **No quote, no fact.** Every stored fact carries a literal span of something the patient actually
   said, in a turn that was theirs. The extractor drops anything else — three conditions, eleven
   lines (`app/extract.py:66`).
2. **Nothing is deleted.** A contradiction retires the old fact; it never removes it. The
   professional can always see what was believed, when, and what replaced it.
3. **The escalation is code.** The red-flag guard is 32 deterministic lines with a negation window.
   The model phrases the escalation; it never decides on one.

---

## 7 · Three verticals, one engine

| Pack | Follows | Red flags |
|---|---|---|
| `rehab` | pain out of ten, sessions a week | sudden sharp pain, a fall, swelling with fever, numbness |
| `postpartum` | symptoms, mood | heavy bleeding, a fever, a bad headache |
| `chronic` | symptoms, a clinical reading, adherence | chest pain or breathlessness, blurred or double vision |

The clinical content is configuration, not code. Adding a fourth vertical is writing a pack —
nothing in the orchestrator, the extractor or the panel knows what rehab is.

---

## 8 · Business

- **Who pays:** the professional, not the patient. A physiotherapist, a midwife, a chronic-care
  nurse — anyone running a caseload of people who should be doing something at home between
  appointments.
- **How:** monthly subscription per professional, tiered by active patients. Market reference:
  Synthflow starts at US$99/month; a lower entry price aimed at Latin America is competitive.
- **Unit economics:** each call costs cents on AssemblyAI's streaming path (333 free hours, then
  US$0.15/hour) and saves a 10–15 minute follow-up call the professional has no time to make.
- **Market:** not "physiotherapists in Argentina" — any health professional doing longitudinal
  follow-up. One engine, many verticals.

---

## 9 · Privacy, on purpose

Health data is **sensitive data** under Argentina's Law 25.326: written informed consent, encryption
in transit and at rest, registration as a data controller, 72-hour breach notification.

**The demo uses 100% fictitious patients and data.** The product is designed for explicit consent
before the first call — not a generic "I accept the terms".

---

## 10 · What is actually built

- The full pipeline runs **with no keys and no database**: `make test` runs 172 tests with no
  environment variable set, and the panel's buttons run the real orchestrator against a scripted
  patient.
- **AssemblyAI in two places:** Universal-Streaming v3 live over the phone call, and Speech
  Understanding on the recording after hangup. Memory feeds `keyterms_prompt`, so the patient's own
  vocabulary from last week primes the recogniser this week.
- **Honest limits:** no authentication, English only, facts land seconds after the hangup rather
  than during the call, and the agent never diagnoses.

---

## 11 · Where the judge sees each criterion

| Criterion | Where |
|---|---|
| Application of Technology | The live transcript on the panel; `GET /calls/{id}/keyterms`; `app/stt.py`, `app/analysis.py` |
| Originality | The fact chain at `/panel`: the 7/10 struck through under the 4/10, each with its quote |
| Business Value | The landing at `/`, whose plain register states the case without jargon |
| Presentation | Week 1 → week 2 with memory off → week 2 with memory on, same patient, in the video |

**constancia** · github.com/gmassello/constancia · MIT
