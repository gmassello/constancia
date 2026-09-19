# Running and deploying

## Three paths

The service degrades on purpose. Pick the shallowest one that shows what you need.

### 1. No keys at all

```bash
uv sync
make test          # 95 green, no network and no database
make web           # builds web/dist (needs node 24 and pnpm)
make dev           # http://localhost:8001 — the landing; the panel is at /panel
```

This is the full demo. The panel's **Call with memory** and **Call without memory** buttons run the
whole pipeline against a scripted patient — the transcript appears turn by turn, the activity rail
lights up as facts land, and the 7/10 knee ends struck through by the 4/10. Both sides of that
transcript are canned: with no `GEMINI_API_KEY` the agent's lines come from `seed/scripts.json`.
*Replay a recorded call* plays a fixture instead, and **Call with a red flag** runs the `alarm` script:
Ana says she fell coming down the stairs, the guard cuts the remaining questions, and the call lands in
the list marked as escalated. None of these buttons can place a real call.

`POST /reset` puts the in-memory seed back where it started, which is what a second take needs.
`bash video/reset.sh --check` is the same idea with a report: it reads the demo state through the API
and says, invariant by invariant, whether it is the one the video expects.

The same thing from the terminal, without building the front end:

```bash
make demo             # week 1: a full call against a scripted patient, trace printed
make demo MEMORY=on   # week 2 over the seed: recall, keyterms and a superseded fact
make fixtures         # re-records seed/replay/*.json from scripted mode
```

### 2. With a Gemini key

```bash
GEMINI_API_KEY=... make demo
```

Same pipeline, real phrasing and real extraction. Still no phone.

### 3. A real phone call

Copy `.env.example` to `.env`, fill it, expose the port, and dial:

```bash
ngrok http 8001                       # PUBLIC_BASE_URL is the https URL it prints
make dev
make smoke PHONE=+54911...            # geographic permissions; spends no LLM or TTS credit
make smoke-stt && make smoke-tts      # the two failure modes that cost the most time
make call PHONE=+54911...
make smoke-analysis URL=<recording url>
```

Run the smokes in that order. `make smoke` places a `<Say>`-only call, so it tells you whether Twilio
will dial that country at all before anything expensive is on the line.

Twilio trial accounts only call verified numbers, and they prepend their own message.

## Environment

`.env` is gitignored; `.env.example` lists every key you have to set, with empty values. **Never
print a secret value, not even truncated.**

### Required

Without all eight, `settings_or_none()` returns `None`: the service still boots, still serves both
pages, still runs `scripted` and `replay` calls and still answers every read endpoint. Only
`mode=live` is refused, with `503`.

| Variable | Notes |
|---|---|
| `GEMINI_API_KEY` | phrasing, extraction and embeddings |
| `ASSEMBLYAI_API_KEY` | live STT and the post-call analysis |
| `ELEVENLABS_API_KEY` | |
| `ELEVENLABS_VOICE_ID` | |
| `TWILIO_ACCOUNT_SID` | |
| `TWILIO_AUTH_TOKEN` | also validates the inbound webhook signature |
| `TWILIO_NUMBER` | validated against E.164 — a malformed number fails at startup, not mid-call |
| `PUBLIC_BASE_URL` | the https URL Twilio reaches; the webhook signature is checked against it |

### Optional

| Variable | Default | Effect |
|---|---|---|
| `DATABASE_URL` | *(empty)* | **The persistence switch.** Set it and the store is Postgres; leave it and the store is the JSON seed. |
| `GEMINI_MODEL` | `gemini-3.8-flash` | |
| `GEMINI_EMBEDDING_MODEL` | `gemini-embedding-001` | |
| `ASSEMBLYAI_SPEECH_MODEL` | `universal-streaming-multilingual` | |
| `ELEVENLABS_MODEL` | `eleven_flash_v2_5` | |
| `VALIDATE_TWILIO_SIGNATURE` | `true` | Turn it off only against a local tunnel you control. |

Four more tuning knobs are defaulted in [`../app/config.py`](../app/config.py) and deliberately left
out of `.env.example`, because nobody needs to set them to run the project: `EMBEDDING_DIMS` (1536,
and it has to match `vector(1536)` in the schema), `LANGUAGE` (`es`), `SILENCE_S` (8.0, how long the
agent waits before re-prompting) and `BARGE_MIN_WORDS` (2, how many words of the patient count as an
interruption).

## The database

Memory needs Postgres with pgvector. Without `DATABASE_URL` the service runs on the seed and the
recall and store phases are skipped — the panel says `data: local seed` in its sidebar either way, so
you can always tell which one you are looking at.

```bash
make db            # pgvector/pgvector:pg17 on localhost:5432
make schema        # applies schema.sql, idempotent
make seed          # Ana, one week-1 call and its facts
uv run pytest -m integration
```

The schema is [`../schema.sql`](../schema.sql), 46 lines, three tables. There is no vector index: the
`ponytail:` marker at the bottom of the file says exact search is fine below about ten thousand rows.

`POST /reset` refuses with `409` when the store is Postgres. It will not wipe a real database.

## Deploying

A multi-stage [`../Dockerfile`](../Dockerfile): a `node:24-slim` stage builds `web/dist`, then a `uv`
stage installs the Python deps, copies `app/`, `schema.sql`, `seed/` and the built front end, and runs
as a non-root user. One image, one service, one public URL — the API serves the pages.

[`../render.yaml`](../render.yaml) declares the Render service: Docker runtime, free plan,
`healthCheckPath: /health`, and the ten environment variables as `sync: false` so none of them are
stored in the repo.

The container binds `${PORT:-8000}`; Render sets `PORT`. Local development uses 8001.

## Checkpoints that need a person

Four things cannot be verified from a terminal alone, because someone has to answer a phone or click
in a dashboard. They are tracked in [`PLAN.md`](PLAN.md):

| | After | What it proves |
|---|---|---|
| C1 | Stage 1 | `make smoke` rings; a real call greets, asks the four questions in order, honours barge-in and says goodbye; the trace shows both sides. |
| C2 | Stage 2 | Two real calls: the second opens on the knee, the 7/10 is superseded by the 4/10 in the database, and `memory=off` does not ask about the knee. |
| C3 | Stage 3 | The panel during a live call: transcript, rail with the highlight, the chain, the chart. |
| C4 | Stage 4 | A public URL reachable from another network, the video, the deck. |

Until C1 happens, [`../app/analysis.py`](../app/analysis.py) has never met a real recording — its
pure functions are tested against a canned AssemblyAI response, and `make smoke-analysis` is what
closes it.

---

The commands themselves are in [`WORKING.md`](WORKING.md).
