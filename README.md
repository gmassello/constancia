# constancia

> An agent that phones the patient every week and remembers what they said last time. A follow-up nobody makes is a plan nobody follows.

## The 30-second version

Patients in home rehab abandon their exercise plan about 70% of the time. Nobody calls to ask how it went, because the professional cannot scale it. **constancia** places the call: it asks the protocol questions in a fixed order, escalates deterministically when a red flag shows up, and — from stage 2 on — opens the next call by asking about what the patient reported the week before, with superseded facts retired instead of deleted.

The same engine serves three verticals as config packs: `rehab`, `postpartum`, `chronic`.

Built for the [lablab.ai × AssemblyAI Voice Agent Hackathon](HACKATHON.md) on **Path B**: AssemblyAI Universal-Streaming v3 over a real phone call, Gemini Flash for phrasing, ElevenLabs for µ-law audio, Twilio Media Streams for the line.

## Where the build is

Stage 2 of four (see `docs/PLAN.md`): **the voice loop plus longitudinal memory**. What works today:

- Outbound Twilio call with a bidirectional `<Connect><Stream>`.
- Live µ-law audio to AssemblyAI Universal-Streaming v3 in Spanish, end-of-turn driven.
- Gemini Flash phrases each turn; the orchestrator decides which question comes next and will not let one be skipped.
- Barge-in: the patient interrupts, the agent stops and the queued audio is cleared.
- Deterministic red-flag guard with negation handling. The LLM only phrases the escalation.
- Per-call trace as an append-only event stream at `GET /calls/{id}/trace`.
- **Memory**: the call opens with every current fact for that patient in the system prompt, and their key
  terms in the STT `keyterms_prompt`. After hangup the transcript is extracted into facts, each grounded in a
  verbatim patient quote and its turn id; a fact that contradicts an old one retires it (`superseded_by` +
  `valid_until`) instead of deleting it. `memory=false` on a call disables recall and store, nothing else.
- `GET /patients/{id}/facts` returns the whole chain, current and retired.

The professional's panel and the deploy land in stages 3 and 4.

## Run it

No keys needed for the offline path:

```bash
uv sync
make test          # 65 tests, no network and no database
make demo          # week 1: a full call against a scripted patient, trace printed
make demo MEMORY=on  # week 2 over the seed: recall, keyterms and a superseded fact
```

With a Gemini key the same demo uses real phrasing:

```bash
GEMINI_API_KEY=... make demo
```

Memory needs Postgres with pgvector. `DATABASE_URL` is optional: without it the service runs, only the
memory phases are skipped.

```bash
make db            # pgvector/pgvector:pg17 on localhost:5432
make schema        # applies schema.sql, idempotent
make seed          # Ana, one week-1 call and its facts
uv run pytest -m integration
```

For a real phone call, copy `.env.example` to `.env`, fill it, expose the port and dial:

```bash
ngrok http 8000                       # PUBLIC_BASE_URL is the https URL it prints
make dev
make smoke PHONE=+54911...            # geographic permissions, no LLM or TTS credit spent
make smoke-stt && make smoke-tts      # the two failure modes that cost the most time
make call PHONE=+54911...
```

## Honest limits

- **No authentication anywhere.** Anything that can reach the URL can place a call. The panel in stage 3 will not fix this: it is out of scope for the hackathon.
- **One worker.** Calls live in an in-process dict. Two instances would not see each other's calls.
- **Extraction runs after hangup**, never during the call: a synchronous write would put dead air on the line.
  The facts land seconds after the patient hangs up, not while they are still talking.
- **~1–1.5 s of silence per turn**: the LLM writes the whole sentence before the TTS starts. Sentence-level streaming is the marked upgrade path.
- Twilio trial accounts only call verified numbers and prepend their own message.
- Spanish only (Rioplatense). The packs are content, not code, so another language is a translation, not a rewrite.

## Layout

| Path | What it is |
|---|---|
| `docs/INTENT.md` | the spec: market, architecture, demo plan, scope |
| `docs/PLAN.md` | the four-stage build order with checkpoints |
| `app/orchestrator.py` | the phase pipeline; the code decides, the LLM phrases |
| `app/channel.py` | the voice loop: Twilio ↔ AssemblyAI ↔ TTS, barge-in |
| `app/packs.py` | the three vertical packs; the only Spanish in the repo |
| `app/guard.py` | the deterministic red-flag guard |
| `app/memory.py` | the fact store: recall, supersession, key terms; `FakeStore` for the offline path |
| `app/extract.py` | structured extraction with span grounding against patient turns |
| `schema.sql` | the whole data model, applied with `make schema` |

MIT licensed.
