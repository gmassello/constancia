# constancia

> An agent that phones the patient every week and remembers what they said last time. A follow-up nobody makes is a plan nobody follows.

## The 30-second version

Patients in home rehab abandon their exercise plan about 70% of the time. Nobody calls to ask how it went, because the professional cannot scale it. **constancia** places the call: it asks the protocol questions in a fixed order, escalates deterministically when a red flag shows up, and — from stage 2 on — opens the next call by asking about what the patient reported the week before, with superseded facts retired instead of deleted.

The same engine serves three verticals as config packs: `rehab`, `postpartum`, `chronic`.

Built for the [lablab.ai × AssemblyAI Voice Agent Hackathon](HACKATHON.md) on **Path B**: AssemblyAI Universal-Streaming v3 over a real phone call, Gemini Flash for phrasing, ElevenLabs for µ-law audio, Twilio Media Streams for the line.

## Where the build is

Stage 1 of four (see `docs/PLAN.md`): **the voice loop end to end, no memory**. What works today:

- Outbound Twilio call with a bidirectional `<Connect><Stream>`.
- Live µ-law audio to AssemblyAI Universal-Streaming v3 in Spanish, end-of-turn driven.
- Gemini Flash phrases each turn; the orchestrator decides which question comes next and will not let one be skipped.
- Barge-in: the patient interrupts, the agent stops and the queued audio is cleared.
- Deterministic red-flag guard with negation handling. The LLM only phrases the escalation.
- Per-call trace as an append-only event stream at `GET /calls/{id}/trace`.

Memory, the professional's panel and the deploy land in stages 2, 3 and 4.

## Run it

No keys needed for the offline path:

```bash
uv sync
make test          # 43 tests, no network
make demo          # a full call against a scripted patient, trace printed
```

With a Gemini key the same demo uses real phrasing:

```bash
GEMINI_API_KEY=... make demo
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

MIT licensed.
