# What constancia is

An agent that phones the patient every week and remembers what they said last time.

## The problem

About seven in ten patients in home rehabilitation abandon their exercise plan. Not because the plan
is wrong — because nobody follows up. A physiotherapist with forty patients cannot make forty calls a
week, so the follow-up simply does not happen, and by the time the patient comes back in, the month
is lost.

The gap is not information. It is attention that scales.

## What it does

constancia places the call. It asks the protocol questions in a fixed order, escalates the moment a
red flag shows up, writes a summary for the professional — and, the following week, **opens by asking
about what the patient said last time**.

That last part is the whole product. Week one:

> — How much does it hurt today from one to ten?
> — My right knee hurts seven out of ten, especially when I climb stairs.

Week two, same patient, same questions:

> — Hi Ana, last week you told me your knee hurt seven out of ten climbing stairs, so I am calling
>   to see how it has been this week.
> — It is four out of ten now.

The 7/10 does not get overwritten. It gets **retired**: it stays in the file, struck through, with
the dates it was true for. The professional opens the panel and sees a chain, not a number.

## Who it is for

**The buyer is the professional**, not the patient. A physiotherapist, a midwife, a chronic-care
nurse — anyone running a caseload of people who are supposed to be doing something at home between
appointments. They pay a subscription and get back the follow-up they cannot make themselves, plus a
file per patient that is built out of the patient's own words rather than out of their memory of the
last consultation.

The patient does not install anything, does not log in, and does not need a smartphone. They answer
their phone.

## What the patient hears

Four questions, in this order, every week (`app/packs.py`, the `rehab` pack):

| | The agent asks about |
|---|---|
| 1 | how much it hurts today out of ten, and at what time of day or with which movement |
| 2 | how many times they did the exercises this week, and whether the routine was hard to keep up |
| 3 | whether there were new complaints after the exercises, like swelling or stiffness |
| 4 | whether they had a fall, a sudden sharp pain, or anything that frightened them |

The agent speaks plain English, two sentences per turn at most, one question at a time, and
never gives a diagnosis or changes a treatment. It interrupts itself when the patient starts talking.

If an answer trips a red flag — a fall, a sudden sharp pain, swelling with fever, numbness — the call
stops asking and escalates. That decision is made by code, not by the model.

## Three verticals, one engine

The clinical content is configuration, not code. A pack declares the prompt fragments, the questions,
the red-flag patterns and what is worth charting:

| Pack | Follows | Red flags |
|---|---|---|
| `rehab` | pain out of ten, sessions a week | sudden sharp pain, a fall, swelling with fever, numbness |
| `postpartum` | symptoms, mood | heavy bleeding, a fever, a bad headache |
| `chronic` | symptoms, a clinical reading, adherence | chest pain or breathlessness, blurred or double vision |

Adding a fourth vertical is writing a pack. Nothing in the orchestrator, the extractor or the panel
knows what rehab is.

## What the professional sees

The panel at `/panel`, one page per patient:

- **How they are doing** — one chart per measure the pack declares, with its scale and whether the
  change is good news. Pain going down is better; sessions going down is not.
- **What the agent remembers** — the fact file. Every entry carries the patient's verbatim words and
  the turn they said them in. A retired entry stays, struck through, with the window it was true for.
- **The live call** — transcript and activity trail as it happens, with each new fact highlighted as
  it lands.
- **The key terms** that primed the speech recognition for that call, which are the patient's own
  vocabulary from the week before.

## Why it is checkable

Two rules make the memory claim inspectable rather than asserted:

1. **No quote, no fact.** Every stored fact must carry a literal span of something the patient
   actually said, in a turn that was theirs. Extraction rejects anything else.
2. **Nothing is deleted.** A contradiction retires the old fact; it never removes it. The professional
   can always see what was believed, when, and what replaced it.

## Honest limits

- No authentication anywhere. This is a hackathon demo with fictitious data, not a product.
- The facts land seconds after the patient hangs up, not while they are still talking.
- English only.
- The agent never diagnoses, never changes a treatment, and never decides on an escalation — it
  detects one deterministically and says so.

---

The market research and the business case behind all of this are in [`INTENT.md`](INTENT.md) §2–§4,
written before the code existed. How it is built is in [`ARCHITECTURE.md`](ARCHITECTURE.md).
