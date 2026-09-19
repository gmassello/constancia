# constancia — voice follow-up engine with longitudinal memory

> An agent that phones the patient every week and remembers what they said last time. A follow-up nobody makes is a plan nobody follows.

Starting spec for the lablab.ai × AssemblyAI **Voice Agent Hackathon**. Covers market validation, architecture, how the project maps to the judging criteria, the demo plan, and what is deliberately out of scope. Deadline: **30 Sep 2026, 12:00 ART**.

> **This is a record, not a reference.** Written on 2026-09-02, before any code existed — its last
> section is called *Before writing code*. Where it disagrees with the repo, the repo is right, and
> the deviation register at the top of [`PLAN.md`](PLAN.md) usually says why. For how the system
> works today, start at [`README.md`](README.md).

---

## 1. Decisions

Closed on 2026-09-02. Everything below assumes these; change them here first.

| Topic | Decision | Why |
|---|---|---|
| Demo vertical | **Home physiotherapy (rehab)** | Visual and concrete: exercises, body parts, pain scores. Best fit for entity detection. Postpartum and chronic stay as config packs. |
| Backend | **Python 3.12 + FastAPI** | AssemblyAI streaming examples and SDK are Python-first; the memory module from `recall` is Python. |
| Telephony | **Real outbound calls via Twilio Media Streams** | The phone ringing is the product. Bidirectional `<Connect><Stream>`, not `<Dial>`. |
| AssemblyAI path | **Path B: Universal-Streaming (Realtime STT)** + pre-recorded API post-call for Speech Understanding | 333 free hours; we own the pipeline; none of the reviewed competitors uses it (section 5). |
| LLM | **Latest Gemini Flash** via the Google AI Studio key (`google-genai` SDK), same model for conversation and extraction | One provider, one key already in hand, fast enough for a voice turn. Verify the exact model ID with `models.list` on day 1. |
| Embeddings | `gemini-embedding-001` with `output_dimensionality=1536`, L2-normalized | Same key as the LLM; `vector(1536)` in the schema stays unchanged. |
| Memory store | **Postgres + pgvector** | Free tier covers hackathon volume. Shipped on Render's managed Postgres, not Supabase. |
| TTS | Any streaming TTS that outputs `ulaw_8000` directly (ElevenLabs does) | Avoids transcoding on the Twilio leg. |
| Memory strategy | **Recall at call start, not per turn** | A patient has fewer than 50 current facts. Load them all into the system prompt; no synchronous vector read inside the turn loop. |
| Red flags | **Deterministic guard in code**, LLM only phrases | Escalation to the professional is a rule in the vertical pack, never a model judgment. |
| Testability | **`ScriptedPatient`** driver + **replay mode** on the deployed URL | Orchestrator runs end to end with no phone and no API keys. The public demo survives a credit outage. |
| Demo A/B | `memory=off` flag on a call | Same patient, same script, memory disabled: the honest "before" take. |
| Deploy | **Render** container (`render.yaml` + Dockerfile) | Media Streams holds a long-lived WebSocket; Lambda does not fit. |
| Video | Produced with the `personal-record-video` skill, `MAX_SECONDS=300` | Screencast of the browser with TTS narration. Call audio is not recorded; the panel's live transcript is what the camera sees. |

## 2. The problem in one sentence

**This is not a product for physiotherapists. It is a conversational follow-up engine with memory, for any health situation where someone has to repeat the same routine week after week and nobody calls to ask how it went.**

The same pattern shows up in all three validated use cases (section 3): the patient starts motivated, gets no regular human follow-up because the professional cannot scale, and drops out. A voice agent that calls, asks specifically about what the person reported last week, and hands the professional a summary of the evolution attacks that pattern directly, above all the missing social contact that a text chatbot never covers well.

## 3. Market validation — three use cases, one engine

### 3.1 Home-based physiotherapy rehab

Patients doing rehab at home (post-surgery, injury, chronic pain) abandon the exercise plan in **about 70% of cases** — systematic review on PubMed ([PMID 26556057](https://pubmed.ncbi.nlm.nih.gov/26556057/), summarized in [this BlueJay Health article](https://medium.com/@bluejayhealth/rate-of-non-adherence-to-home-based-pt-is-70-can-telerehabilitation-improve-the-compliance-rate-3b3123768694)). Documented causes: no real intention to follow the program, low self-motivation, negative attitudes toward exercise, little social support.

### 3.2 Postpartum follow-up

**56% to 60% of new mothers** miss key six-week postpartum checks ([Cedar Gate](https://www.cedargate.com/resources/cedar-gate-data-finds-nearly-60-of-new-mothers-miss-essential-postpartum-follow-up-care/), [Axios](https://www.axios.com/2025/08/04/new-moms-miss-postpartum-appointments-weeks)), leaving undetected cardiovascular risk ([American Heart Association](https://www.heart.org/en/news/2023/11/27/gaps-in-postpartum-care-may-leave-many-women-at-risk-for-cardiovascular-disease)). A UCL study found more than 40% miss key postnatal check-ups ([UCL News](https://www.ucl.ac.uk/news/2020/nov/over-40-women-may-be-missing-key-postnatal-check-ups)). The check is short and conversational (bleeding, mood, breastfeeding, pain): a natural fit for voice, and the best-documented number of the three.

### 3.3 Remote monitoring of chronic disease (diabetes, hypertension)

Remote monitoring programs show significant attrition within weeks of starting, documented for diabetes ([MDPI](https://www.mdpi.com/2227-9032/13/7/698)) and hypertension ([AJMC](https://www.ajmc.com/view/effect-of-remote-patient-monitoring-on-stage-2-hypertension)). Same pattern: high initial motivation, decay without regular human contact. Largest vertical by patient volume, but needs more integration (devices, clinical values) than the other two.

### Why it is not solved already

Reviewed the voice-AI-for-health landscape ([full list at Prosper AI](https://www.getprosper.ai/blog/voice-ai-systems-for-patient-call-automation)): Prosper AI, Assort Health, Hyro, Infinitus, SuperDial, Retell AI, Synthflow, Rasa, CloudTalk, EliseAI Health. All of them solve discrete, one-off tasks: book an appointment, verify coverage, single-call intake. **None does longitudinal follow-up of one patient across weeks, remembering the full history of previous conversations, in any of the three verticals.** Cross-checked against other lists: [Rasa](https://rasa.com/blog/ai-voice-agents-for-healthcare-top-platforms-for-2026), [Retell AI (HIPAA compliance)](https://www.retellai.com/blog/10-best-hipaa-compliant-ai-voice-agents-for-healthcare-clinics), [Parloa](https://www.parloa.com/blog/ai-voice-agents-in-healthcare/).

Pricing of what does exist: Retell AI about US$0.07/minute, Synthflow from about US$99/month, aimed at mid-size or large clinics, not at an independent professional with 30-40 active patients.

**The gap is twofold: product (nobody does longitudinal memory, in any vertical) and price (nobody targets small practices or independents). It is the same gap in all three use cases, which is why the generic engine is worth building instead of a single-niche app.**

## 4. Business model (deck — Business Value)

- **Who pays:** the independent professional or small health center (physiotherapist, obstetrician/midwife, diabetes center), not the patient. Same buyer in all three verticals: someone who does follow-up by hand today because there is no alternative.
- **Suggested price:** monthly subscription per professional, tiered by active patients in follow-up (e.g. up to 20 / up to 50 / unlimited). Market reference: Synthflow starts at US$99/month for low volumes; a similar or lower entry price aimed at Latin America is competitive.
- **Why it is profitable:** each call costs cents on Path B, and it saves the professional a 10-15 minute follow-up call they have no time to make, or simply do not make, which is why the patient drops out.
- **Why multi-vertical helps the pitch:** the addressable market is not "physiotherapists in Argentina", it is "any health professional doing longitudinal follow-up". Much larger, and "one engine, many verticals" shows product vision instead of a single use case.
- **Impact metrics for the deck** (one per vertical, pick the strongest for the audience):
  - Rehab: "of 10 patients in home rehab, about 7 abandon the plan without active follow-up."
  - Postpartum: "of 10 new mothers, 5 to 6 miss a key postpartum check."
  - Chronic: "remote monitoring programs for diabetes and hypertension lose patients steadily without regular human contact."

## 5. Hackathon fit — rules, criteria, competition

Source: [lablab.ai/ai-hackathons/assemblyai-voice-agent-hackathon](https://lablab.ai/ai-hackathons/assemblyai-voice-agent-hackathon)

- **Window:** 1–30 Sep 2026, closes 30 Sep 12:00 ART. Registration open for the whole window.
- **Team:** 1 to 6 people. Solo is allowed: create a team of one on the platform and register on the Discord.
- **Prize:** 5 winners, US$1,000 cash + US$1,000 in AssemblyAI credits each (no ranking, all equal).
- **Two technical paths:**
  - *Path A — Voice Agent API* (all-in-one: STT + LLM + TTS + turn-taking + tool calling), about US$4.50/hour, unconfirmed whether it is in the free tier.
  - *Path B — Realtime Speech-to-Text* (STT only, you build LLM and TTS), about US$0.15/hour, **333 free hours in the free tier**. This is our path.
- **Mandatory deliverables:** public GitHub repo with MIT license, demo video (max 5 min), deck/slide presentation, deployed app with a public URL.
- **Judging criteria** (no published weights, assume 25% each): *Application of Technology*, *Presentation*, *Business Value*, *Originality*.

### How the project hits each criterion

- *Application of Technology* — Universal-Streaming live on camera (the transcript panel), plus Speech Understanding on the recorded call after it ends (entity detection for symptoms and body parts, sentiment for frustration or low motivation). Memory also feeds the STT: the patient's current facts become `keyterms_prompt` for the next call, so recognition of their exercise names and medications improves week over week.
- *Business Value* — a concrete, citable number (70% non-adherence) and a clear model (subscription per professional, section 4).
- *Originality* — **the agent recalls and acts on what the patient said weeks ago, with superseded facts retired. Not a score chart, not a transcript archive.** No listed platform and no reviewed competitor does this (table below).
- *Presentation* — the demo moment is simple and decisive: call 1 → call 2 a week later → the agent opens by asking specifically about what the patient reported the first time, without being told.

### Competitors reviewed on 2026-09-02

| Repo | Voice input | AssemblyAI usage | Memory across sessions | Phone |
|---|---|---|---|---|
| [VoiceMed](https://github.com/rehannayeem0786/Voicemed-AI-Agent-Hackathon) (medical triage) | browser mic | Voice Agent API, 6 tools, 44 tests | No: SQLite sessions with no patient identity, written and never read back | No |
| [MockMate](https://github.com/kingxjayant/mockmate-voice-interview-coach) (mock interviews) | browser mic | Voice Agent API | Partial: localStorage score history, never injected into the prompt | No |
| [Relay](https://github.com/Akixama/relay) (field ops) | browser mic | Voice Agent API | No: static seed data about machines | No |
| [InterviewLab](https://github.com/ArifbillahKamil/InterviewLab-AssemblyAI) | browser mic | Voice Agent API, tests, live deploy | No: JSON files on disk, never re-read | No |
| [Storefront](https://github.com/sahariarhossain524-sketch/Modern-E-commerce-Storefront) | none | not used | N/A | No |
| [smartlink `voice-agent-demo`](https://github.com/amrorama55-source/smartlink-api/tree/voice-agent-demo) | simulated (`setTimeout` + `speechSynthesis`) | not used | No | No |

Takeaways: all four real entries use Path A; none uses Streaming v3, Speech Understanding, or telephony; none remembers a user between sessions. Where they beat us today is evidence, not the idea: VoiceMed ships 44 tests and a live smoke test, MockMate a deck, a public URL and an offline demo mode, InterviewLab a deploy with a health endpoint. Section 12 closes that gap. None of the six has a recorded video yet.

## 6. Architecture

### 6.1 One call is a phase pipeline

Not a free-running agent loop. Each call runs fixed phases; each phase is `(name, fn, critical)`. Non-critical phases fail soft with a warning event and the call continues.

```
greet     → open with the pack's greeting, patient name
recall    → load current facts for this patient (all of them, sorted by reported_at)
            → into the system prompt
            → their key terms into the STT keyterms_prompt        [non-critical]
converse  → question protocol from the vertical pack, tracked in code:
            pain → adherence → side effects → red flags.
            The LLM phrases; the orchestrator decides which question is next
            and will not let one be skipped.
            Red-flag guard runs on every patient turn (6.4).
extract   → structured fact extraction from the transcript (6.3)  [non-critical]
store     → embed + insert facts, supersede old ones, persist call [non-critical]
summarize → render the professional's weekly summary from the fact set
```

`memory=off` on a call disables `recall` and `store`. Everything else runs identically. That is the A/B in the demo.

> **Built differently.** `recall` runs **before** `greet`, not after — that is deviation 7 in
> [`PLAN.md`](PLAN.md), and it is what lets the agent open on the knee. The six phases as shipped are
> in [`ARCHITECTURE.md`](ARCHITECTURE.md).

### 6.2 Memory: never delete, invalidate

Reference pattern: [Auto Interview AI — Persistent Memory for Voice AI Agents](https://www.autointerviewai.com/blog/persistent-memory-voice-ai-agents-vector-database-architecture-2026), adapted with what worked in `recall` (temporal invalidation) and `ringdown` (span-grounded extraction).

```
┌──────────────────────────────────────────────────────────┐
│  CALL START                                               │
│   1. Load every fact where valid_until is null and        │
│      superseded_by is null, for this patient.             │
│      → system prompt, newest first, with reported_at.     │
│      → key terms → STT keyterms_prompt.                   │
│  DURING THE CALL                                          │
│   2. Session buffer: last 10-15 turns, in-process dict    │
│      keyed by call id. No Redis.                          │
│      ponytail: single worker; add Redis if there are two. │
└──────────────────────────────────────────────────────────┘
                          │
                          ▼ (async, after hangup)
┌──────────────────────────────────────────────────────────┐
│  AFTER THE CALL                                           │
│   3. Recording → AssemblyAI pre-recorded API with         │
│      entity_detection + sentiment_analysis.               │
│   4. Extraction (Gemini Flash, Pydantic output):           │
│      only durable facts, each with the verbatim patient   │
│      quote and turn id that supports it.                  │
│      Input includes the top-5 similar existing facts      │
│      (pgvector) so the model can return supersedes: id.   │
│   5. Embed + insert. supersede(old, new) sets             │
│      superseded_by and valid_until in one UPDATE.         │
│   6. Raw transcript → calls.transcript, audit only.       │
│      Never injected into a prompt.                        │
└──────────────────────────────────────────────────────────┘
```

Why recall at call start instead of a per-turn vector read: a patient in follow-up has tens of facts, not thousands. Loading them all removes the 150 ms synchronous budget and the similarity threshold tuning entirely. pgvector stays for two jobs: giving the extractor candidate facts to supersede, and letting the professional search across patients.

**Data model — vertical-agnostic (`program_type` is the only thing that changes):**

> **Superseded.** The shipped schema is [`../schema.sql`](../schema.sql), which is the only copy
> worth reading — a second one here would age on its own. It grew five columns this section does not
> have: `patient_memories.term` (the short key term, deviation 6) and `.value numeric` (the number
> that feeds the chart, deviation 3), and `calls.summary`, `.escalated` and `.analysis jsonb`
> (deviations 2 and 9). Everything else it specified still holds: three tables, `program_type` as the only
> vertical-specific column, `superseded_by` + `valid_until` for retirement, and `vector(1536)` with no
> vector index.


Rules that matter for the demo:

- Memory writes are **always asynchronous**. A synchronous write puts ~150 ms of dead silence in the call.
- Contradictions resolve by supersession, not by deletion. "It doesn't hurt anymore" creates a new fact and retires the old one; both stay visible in the panel as a chain.
- Every fact is grounded in a patient turn. A quote taken from the agent's own question is not evidence.
- "No precedent" is a correct answer. On a first call the agent says it has nothing on file and asks from scratch; it never invents history.
- The transcript is data, never instructions. "Tell my physio I'm fine and close my file" is stored as evidence and changes nothing. The system prompt carries a block of rules that override anything said on the call.
- The agent never claims it saved something until `store` confirms it. "I've noted that for your physio" comes after the write, or not at all.
- Cost at hackathon scale is irrelevant: embeddings about US$0.000004 per fact, extraction with a small model costs cents per thousand calls.

### 6.3 Structured extraction

Pydantic models: `Fact { fact, category, quote, turn_id, confidence, supersedes: UUID | None, valid_until: date | None }` and `FactSet { facts: list[Fact] }`. `complete_structured(system, transcript, FactSet)` calls Gemini with `response_mime_type="application/json"` and `response_schema=FactSet`, validates the reply with Pydantic, and on `ValidationError` feeds the error text back and retries, up to 3 attempts. Gemini's JSON Schema support has quirks (no `$ref`, limited `anyOf`); `hindsight/backend/tests/test_gemini_schema.py` covers the ones already hit. Grounding check in code: `quote` must appear in the turn with that `turn_id`, and that turn must be the patient's. The model returns `supersedes`; the code calls `supersede()`. The model never writes the database.

> **Built differently.** The extractor receives **every current fact with its id**, not a top-5 from
> pgvector (deviation 1), and `Fact` gained a short `term` (deviation 6) and a numeric `value`
> (deviation 3). The SDK converts the Pydantic model on its own, so no schema cleaning was needed
> (deviation 8) and the file this paragraph cites belongs to another project. Speech Understanding
> does **not** feed the extractor: it runs on the recording after hangup and lands in
> `calls.analysis` (deviation 2). What ships is in [`BACKEND.md`](BACKEND.md).

### 6.4 Vertical packs and the red-flag guard

`VerticalPack` is the only thing that differs between verticals, chosen at patient creation and frozen:

```
VerticalPack
  key: 'rehab' | 'postpartum' | 'chronic'
  prompt_fragments: { greet, converse, summarize }
  questions: ordered list the orchestrator tracks (converse phase)
  keyterm_categories: which fact categories feed the STT keyterms_prompt
  red_flags: list of (rule, message) — deterministic matchers on patient turns
  escalation: what to do when a red flag fires (flag the call, tell the patient
              to contact the professional now, end the protocol early)
```

Three packs exist from day one (`rehab`, `postpartum`, `chronic`); only `rehab` gets demo data. Building the pack layer early is what makes the "platform" claim credible to a judge.

The red-flag guard produces a record `{input, value, rule, branch}` per hit. Whether a call escalates is that record, not a model opinion. The LLM only phrases the escalation message. Rehab examples: sudden sharp pain, fall, swelling with fever, numbness.

### 6.5 ScriptedPatient and replay

`ScriptedPatient` implements the same interface as the live STT stream and answers from a script. Tests, `make demo` and evaluation run the real orchestrator with no phone and no API keys; `--live` swaps in Twilio + AssemblyAI. The deployed URL also serves a **replay** of a recorded call (transcript + extraction events) so the demo works when credits run out on judging day.

### 6.6 Professional's panel

- **One query module** computes everything the panel, the API and the agent's summary show. A number on screen and a number the agent says on the phone cannot diverge.
- **Live transcript over SSE** with a per-call replay buffer (last 500 events), keep-alive comments, and reconnect with backoff in the browser. Opening the panel mid-call shows the call from the start, then live.
- **Activity rail:** every turn and every extracted fact, verbatim, with a 4-second highlight when a new fact lands or an old one is superseded. Provenance on screen is what makes the memory claim believable.
- **Weekly evolution chart** with no charting library: divs with proportional height and the value printed as text.
- **Per-call trace** as one append-only event stream, rendered as JSON or HTML depending on the `Accept` header.

## 7. Twilio and the voice loop

This is the one piece none of the previous projects prototyped. It is the biggest risk, so it is **build stage 1**, before memory and before the panel.

- **Outbound call:** `client.calls.create(to, from_, url=PUBLIC_BASE_URL + "/voice?call_id=...", record=True, recording_status_callback=...)`.
- **TwiML:** `<Connect><Stream url="wss://.../media/{call_id}">`, bidirectional.
- **Inbound audio:** Twilio sends `media` messages with base64 µ-law 8 kHz. Forward to AssemblyAI Streaming v3 (`wss://streaming.assemblyai.com/v3/ws`) with `sample_rate=8000`, `encoding=pcm_mulaw`, and the patient's `keyterms_prompt`. Use end-of-turn events, not raw partials, to trigger the LLM.
- **Outbound audio:** TTS streamed in `ulaw_8000` and sent back as `media` messages in the same WebSocket. Send a `mark` after each utterance to know when playback ends.
- **Barge-in:** on a new patient turn while the agent is speaking, send `clear` to Twilio and cancel the in-flight TTS.
- **Webhooks:** `/voice` (TwiML), `/voice/status`, `/voice/recording` (accept only `https://api.twilio.com/` URLs). Validate `X-Twilio-Signature` against `PUBLIC_BASE_URL + path`, never `request.url` (behind a proxy it arrives as `http://` and fails). `VALIDATE_TWILIO_SIGNATURE=false` for local dev.
- **Post-call:** recording → AssemblyAI pre-recorded API with `entity_detection` and `sentiment_analysis`; the results join the live transcript as input to extraction. Verify feature availability against the current AssemblyAI docs before relying on it.
- **Smoke test:** `scripts/test_outbound.py`, 20 lines, places a call with `<Say>` to validate geographic permissions before spending any LLM or TTS credit.
- **Config:** `pydantic-settings`, cached `get_settings()`, E.164 validated at boot, the process refuses to start without its secrets. Ranking weights and phase timeouts live in the same `Settings`.
- **Latency:** Twilio times a webhook out at 15 s and a Render free instance sleeps after 15 min. Wake the service with `curl` before any demo, or run a paid instance during the judging window.
- **LLM calls:** retry with exponential backoff on 429 and 5xx, typed errors, tokens and elapsed time emitted as trace events. A rate limit mid-call is the most likely live failure; on the AI Studio free tier that is the per-minute request cap, so check the quota of the chosen model before the demo.

## 8. Privacy notice — matters for the demo, not only for production

Health data is **sensitive data** under Argentina's Law 25.326. Handling it for real requires written informed consent (not a generic "I accept the terms"), encryption at rest and in transit, registration as a data controller with the RNBD, and incident notification within 72 hours ([summary by Estudio Nunes & Asociados](https://estudionunes.com.ar/proteccion-de-datos-sensibles-lo-que-las-empresas-deben-saber/)).

**For the hackathon: 100% fictitious patients and data in the demo.** Real legal compliance is not needed to win, but one line in the deck ("designed with Law 25.326 in mind, explicit consent before the first call") earns Business Value points because it shows the product was thought past the weekend prototype.

## 9. Demo plan (5-minute video)

The demo shows **one** vertical (rehab); one slide and one narration line make explicit that the engine serves the other two. Produced with the `personal-record-video` skill: narration is TTS from `video/narration.tsv` (`caption` and `speak` columns so numbers are read as words), the human records the browser window with the mic off, the video is fitted to the audio afterwards. **The call audio is not on the recording.** What the camera sees is the panel with the live transcript of both sides while the phone rings off camera. The human plays the patient on the phone and reads lines from the shot list.

| # | Beat | Length | On screen |
|---|---|---|---|
| 1 | The problem | 20 s | One slide: 7 of 10 home-rehab patients abandon without follow-up. |
| 2 | The product in one sentence | 30 s | "An agent that phones your patients and remembers every previous conversation." Small slide: rehab / postpartum / chronic, same engine, different pack. |
| 3 | Call 1, live | 70 s | New fictitious patient, Ana. The agent says it has nothing on file and asks from scratch. Ana reports right-knee pain 7/10 climbing stairs and skipping the exercises twice this week. Live transcript on the panel; facts land in the rail with highlight. 🎯 |
| 4 | Call 2, `memory=off` | 40 s | "One week later." Same patient, memory disabled: the agent asks the generic protocol, nothing about the knee. Short, honest "before". |
| 5 | Call 2, memory on | 60 s | Same patient, memory on. The agent opens by asking about the right knee on stairs. Ana says it is down to 4/10. On the panel the 7/10 fact is superseded live and the new one appears. 🎯 This is the moment that sells the project. |
| 6 | The professional's panel | 40 s | Weekly evolution, the superseded chain, the keyterms that fed the STT, one red-flag example from the seed. |
| 7 | Close | 20 s | Business model slide, endcard with name, URL, repo, MIT. |

Total: 280 s, under the 300 s cap. If it runs long, cut beat 4 to 25 s first, then beat 6.

Before recording: `video/reset.sh --check` must be all green (seeded patient exists, week-1 facts present, no call in flight, no facts from previous takes). The shot list marks money shots and includes a "what can come out differently" section: the agent is non-deterministic, so film what it actually said and rewrite the narration line rather than re-shooting for a prettier sentence.

> **Built differently.** Beats 1 and 2 are filmed on the **public landing**, not on slides: it exists,
> it says the same thing and it would otherwise be a second copy to keep in sync. Beat 6 shows a red
> flag **happening** — the panel's *call with a red flag* button runs the `alarm` script and the guard
> cuts the call on camera — instead of pointing at one in the seed. The shot list as written is
> [`video-script.md`](video-script.md), the narration is [`../video/narration.tsv`](../video/narration.tsv),
> and the track measures 3:12 against the 5:00 cap.

## 10. Project name

**constancia**. Spanish for adherence, consistency, keeping at it. Works as a proper name, is honest about what the product solves, and speaks to the general pattern (follow-up + memory) rather than one specialty. It follows the shelf: `recall`, `hindsight`, `ringdown` — short, lowercase, a little evocative. Constancia is ringdown's clinical counterpart: an agent that phones a human and proves what happened.

## 11. Stack

- **Backend:** Python 3.12, FastAPI, `websockets`, `psycopg` with thin helpers (`fetch`, `execute`, `to_vector_literal`, `init_schema`), no ORM, no migration framework: `schema.sql` applied idempotently with `python -m app.db`.
- **STT:** AssemblyAI Streaming v3 (`wss://streaming.assemblyai.com/v3/ws`), µ-law 8 kHz. Pre-recorded API post-call for entity detection and sentiment.
- **LLM:** latest Gemini Flash via `google-genai` for conversation and extraction.
- **TTS:** streaming, `ulaw_8000` output (ElevenLabs or equivalent).
- **Memory:** Postgres + pgvector, `gemini-embedding-001` at 1536 dims.
- **Telephony:** Twilio Programmable Voice, Media Streams.
- **Panel:** React + Vite + TypeScript, no charting library, no UI framework. SSE for live events.
- **Deploy:** one Render container — FastAPI serves the pages too, so there is no separate front-end host (deviation 4). Public `/health` endpoint.
- **Tooling:** `Makefile` (`make dev / test / demo / deploy`), pinned exact versions.

> **Built differently.** There is no `make deploy`: Render deploys from the repo, and the sixteen
> targets that do exist are listed in [`WORKING.md`](WORKING.md). The panel is a Vite multi-page
> project under `web/`, not `panel/` (deviation 17), and it is bilingual with a light default theme
> (deviations 19 and 20), not English-only and dark.

## 12. MVP scope and out of scope

### In scope for the hackathon

- One professional, hardcoded. Patients created by seed script.
- Three vertical packs; demo data only for `rehab`.
- Outbound call to one real phone number, full voice loop, barge-in.
- Memory: recall at call start, extraction, supersession, keyterms into STT.
- Red-flag guard with at least three rehab rules.
- `ScriptedPatient`, replay mode, tests over the orchestrator with no network.
- Professional's panel: live transcript, activity rail, weekly evolution, superseded chain.
- Deterministic seed with relative dates (`age_days`), no randomness, committed JSON. The seed plants the contradiction pair (7/10 → 4/10) and one red flag.
- Day-one files: `HACKATHON.md` (rules transcribed), `SUBMISSION.md` (`criterion | how we show it | where the judge sees it | status`), `docs/video-script.md`, `CLAUDE.md` (hard rules: all repo output in English, pin exact versions, no secrets in git).

> **Built differently.** Those files live in `docs/` now, and the hard rules moved to
> [`../AGENTS.md`](../AGENTS.md), which every coding agent reads on its own; the `CLAUDE.md` files
> are one-line pointers at it. [`README.md`](README.md) is the index.
- README with a "The 30-second version" block, a judging-criteria table, an "Honest limits" section written as the build goes, and a `[!WARNING]` about the panel having no real authentication.

### Out of scope

- Authentication and multi-tenancy on the panel.
- A weekly scheduler with idempotent dialing and a "call may have landed" error taxonomy. The demo triggers calls by hand.
- Hash-chained audit log and a test that asserts published numbers against generated artifacts. Only if a metric gets published.
- Memory exposed as LLM tools. Unnecessary with recall at call start.
- A feedback document on the AssemblyAI API. Only if the hackathon has a feedback prize.
- Real legal compliance (consent flow, encryption policy, RNBD registration).
- Device integration for the chronic vertical.

## 13. Definition of done

- [ ] Public GitHub repo, MIT license visible in the About section.
- [ ] Deployed backend with a public `/health` and the panel reachable at a public URL, tested from another network.
- [ ] Demo video under 5 minutes, captions burned in, uploaded public or unlisted.
- [ ] Deck (or `docs/devpost.md` equivalent plus endcard) submitted.
- [ ] `make test` green: orchestrator with `ScriptedPatient`, extraction grounding, supersession, red-flag guard, import safety with no env.
- [ ] `scripts/test_outbound.py` places a real call.
- [ ] The week-1 → week-2 moment works in `--live` and in replay.
- [ ] `video/reset.sh --check` all green before the final take.
- [ ] `SUBMISSION.md` has evidence (file path, URL or video timestamp) on every row.

## 14. Before writing code

1. Register on [lablab.ai](https://lablab.ai/ai-hackathons/assemblyai-voice-agent-hackathon) (team of one) and join the Discord.
2. Claim the AssemblyAI API credits (signup link on the hackathon page).
3. Install the official Agent Skill before writing code: `npx skills add AssemblyAI/assemblyai-skill` (keeps the LLM from hallucinating deprecated AssemblyAI APIs).
4. Gemini: run `models.list` with the AI Studio key, pin the exact Flash model ID and the embedding model, make one test call of each, and note the free-tier quota.
5. Twilio: buy a number with voice capability, enable geographic permissions for Argentina, run the `<Say>` smoke test.
6. Write `HACKATHON.md` and `SUBMISSION.md` first; every row without evidence is unfinished work.
7. Build stage 1: the voice loop end to end with a hardcoded prompt and no memory. Nothing else until a real phone rings and answers.
8. Seed data for 1-2 fictitious patients, including the contradiction pair and one red flag.

---

*Research done on 2026-09-02. Sources cited inline. Competitor review and prior-project patterns (`recall`, `hindsight`, `ringdown`, `afterimage`, `sundae-metrics`, `adlc`) reviewed the same day.*
