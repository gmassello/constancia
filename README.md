# constancia

> An agent that phones the patient every week and remembers what they said last time. A follow-up nobody makes is a plan nobody follows.

## The 30-second version

Patients in home rehab abandon their exercise plan about 70% of the time. Nobody calls to ask how it went, because the professional cannot scale it. **constancia** places the call: it asks the protocol questions in a fixed order, escalates deterministically when a red flag shows up, and — from stage 2 on — opens the next call by asking about what the patient reported the week before, with superseded facts retired instead of deleted.

The same engine serves three verticals as config packs: `rehab`, `postpartum`, `chronic`.

Built for the [lablab.ai × AssemblyAI Voice Agent Hackathon](HACKATHON.md) on **Path B**: AssemblyAI Universal-Streaming v3 over a real phone call, Gemini Flash for phrasing, ElevenLabs for µ-law audio, Twilio Media Streams for the line.

## Where the build is

Stage 3 of four (see `docs/PLAN.md`): **the voice loop, longitudinal memory and the professional's panel**. What works today:

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
- **The professional's panel** at `/`: patient list, weekly chart, the supersession chain with the verbatim
  quote and turn id behind every fact, the key terms that fed the STT, and the live call — transcript and
  activity rail over SSE, with the new facts highlighted as they land.
- **Three call modes.** `live` dials a real phone. `scripted` runs the whole pipeline against a scripted
  patient, with no phone and no keys. `replay` replays a recorded call at its original pace. The last two are
  what make the demo survive an outage.
- **After hangup** the recording goes to AssemblyAI's pre-recorded API for entity detection and sentiment,
  stored in `calls.analysis`.

The deploy, the video and the deliverables land in stage 4.

> [!WARNING]
> There is no authentication anywhere. Anything that can reach the URL can read every patient's history and
> place a call. This is a hackathon demo with fictitious data, not a product.

## Run it

No keys needed for the offline path:

```bash
uv sync
make test          # 89 tests, no network and no database
make panel         # builds panel/dist (needs node 24 and pnpm)
make dev           # http://localhost:8000 — the panel, on the seed
```

In the panel, **Llamar ahora** in mode *simulada* runs a whole call with no phone and no keys: the transcript
appears turn by turn, the rail lights up as facts land, and the 7/10 knee is struck through by the 4/10.
Uncheck *memoria* and the same call starts from scratch — that is the honest A/B.

`POST /reset` puts the in-memory seed back where it started, which is what a second take needs.

Without the panel built, the same thing from the terminal:

```bash
make demo            # week 1: a full call against a scripted patient, trace printed
make demo MEMORY=on  # week 2 over the seed: recall, keyterms and a superseded fact
make fixtures        # re-records seed/replay/*.json from the scripted mode
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
make smoke-analysis URL=<recording url>   # entity detection and sentiment on a real recording
```

## Honest limits

- **No authentication anywhere.** Anything that can reach the URL can place a call. The panel in stage 3 will not fix this: it is out of scope for the hackathon.
- **One worker.** Calls live in an in-process dict. Two instances would not see each other's calls.
- **Extraction runs after hangup**, never during the call: a synchronous write would put dead air on the line.
  The facts land seconds after the patient hangs up, not while they are still talking.
- **~1–1.5 s of silence per turn**: the LLM writes the whole sentence before the TTS starts. Sentence-level streaming is the marked upgrade path.
- **The replay fixtures are still synthetic.** `seed/replay/*.json` come from the scripted mode, not from a
  real call. They get re-recorded from `GET /calls/{id}/export` once a real call happens.
- **`app/analysis.py` has never met a real recording.** Its pure functions are tested against a canned
  AssemblyAI response; `make smoke-analysis` is what closes it. If Twilio's media needs basic auth, the
  recording has to be downloaded and re-uploaded instead of passed by URL.
- **Calls live in memory.** After a restart the panel loses the live trace of past calls; the history comes
  from the database instead.
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
| `app/queries.py` | the single reducer module: the chain, the weekly series, the key terms of a past call |
| `app/replay.py` | the two modes that need no phone: scripted and recorded |
| `app/analysis.py` | post-call entity detection and sentiment on the recording |
| `panel/` | the professional's panel: React 19 + Vite, no UI or charting library |
| `schema.sql` | the whole data model, applied with `make schema` |

MIT licensed.
