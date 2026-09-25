# Running and deploying

## Three paths

The service degrades on purpose. Pick the shallowest one that shows what you need.

### 1. No keys at all

```bash
uv sync
make test          # 311 tests, no network and no database
make web           # builds web/dist (needs node 24 and pnpm)
make dev           # http://localhost:8001 — the landing; the panel is at /panel
make take          # the same server without --reload, for a recording session
```

This is the full demo. The panel's **Call with memory** and **Call without memory** buttons run the
whole pipeline against a scripted patient — the transcript appears turn by turn, the activity rail
lights up as facts land, and the 7/10 knee ends struck through by the 4/10. Both sides of that
transcript are canned: with no `GEMINI_API_KEY` the agent's lines come from `seed/scripts.json`.
*Replay a recorded call* plays a fixture instead, and **Call with a red flag** runs the `alarm` script:
Ana says she fell coming down the stairs, the guard cuts the remaining questions, and the call lands in
the list marked as escalated. None of these buttons can place a real call.

**Call without memory** runs the week-1 script, because the script is chosen by what the agent has in
its prompt and memory off leaves it with nothing. That makes it week one, not the other side of the
A/B: for that, *the same call without memory* runs `week2-off` — the week-2 answers with the generic
agent lines — so the two calls differ in the memory and in nothing else.

`POST /reset` puts the in-memory seed back where it started, which is what a second take needs.
`bash video/reset.sh --check` is the same idea with a report: it reads the demo state through the API
and says, invariant by invariant, whether it is the one the video expects. It then spends one request
on Gemini and one on AssemblyAI and compares `PUBLIC_BASE_URL` against the tunnel ngrok is actually
serving, because those three fail in silence: a spent quota, a rejected key and a stale tunnel all
surface as a phone that rings and an agent that says nothing. No key is printed.

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
make smoke-call                       # the six phases against the real LLM, no phone
make call                             # dials DEMO_PHONE; make call PHONE=+54911... overrides it
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
pages, still runs `scripted` and `replay` calls, and still answers every read endpoint the seed store
can serve. `mode=live` is refused with `503`, and so is `GET /search`, which needs pgvector.

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
| `DEMO_PHONE` | *(empty)* | The number a seeded patient is dialled at. The seed carries no phone, so without this a `mode=live` call on a seeded patient is a `400`. Resolution order is `request.phone`, then the patient row, then this. A real number is personal data: it never gets committed. |
| `DATABASE_URL` | *(empty)* | **The persistence switch** — but only with the eight required variables also set, because the store is chosen from `settings_or_none()`, which returns `None` without them. With it, the store is Postgres and the schema is applied at boot; without it, the store is the JSON seed. |
| `GEMINI_MODEL` | `gemini-3.8-flash` | |
| `GEMINI_EMBEDDING_MODEL` | `gemini-embedding-001` | |
| `ASSEMBLYAI_SPEECH_MODEL` | `universal-3-6-pro` | A model offered *by* Universal-Streaming, not a different product: same `wss://streaming.assemblyai.com/v3/ws`, same API version. It was picked by measurement, not preference — on a real 8 kHz call it transcribed the patient's line verbatim where `universal-streaming-english` returned "My hair is 7 out of 10". The API rejects an unknown value and lists the ones it takes in the error, which is how the name was pinned. |
| `ELEVENLABS_MODEL` | `eleven_flash_v2_5` | |
| `AI_GATEWAY_API_KEY` | *(empty)* | The second opinion on promises. Without it [`../app/jev.py`](../app/jev.py) returns `None` before opening a socket and the deterministic rules decide alone — the three generic ones in `app/commitments.py` plus the vertical's own `pack.actions` — which is what every test and every offline demo does. A Vercel AI Gateway key, not a TypeSafe one: TypeSafe paused signups, and the gateway is the documented way in. |
| `VALIDATE_TWILIO_SIGNATURE` | `true` | Turn it off only against a local tunnel you control. |

Seven more tuning knobs are defaulted in [`../app/config.py`](../app/config.py) and deliberately left
out of `.env.example`, because nobody needs to set them to run the project: `EMBEDDING_DIMS` (1536,
and it has to match `vector(1536)` in the schema), `LANGUAGE` (`en`), `SILENCE_S` (8.0, how long the
agent waits before re-prompting), `BARGE_MIN_WORDS` (2, how many words of the patient count as an
interruption), `STT_CONFIDENCE_FLOOR` (0.6, below which a number the recogniser heard earns one
read-back turn; `0` switches the read-back off entirely) `JEV_FLOOR` (0.8, how sure Jev has to be
before a sentence every vocabulary rejected still counts as a promise) and `JEV_ZERO_RETENTION`
(`false`). That last one is not a preference: Zero Data Retention is a Pro tier, and asking for it on
a hobby plan is not ignored — the gateway answers **403 on every call**, which the client turns into a
`None` that looks exactly like the vocabulary deciding. Turn it on only on a plan that has it, and
`make smoke-jev` is how you find out.

`JEV_FLOOR` is measured, not chosen. `make smoke-jev` posts the sentences the deterministic rules
reject, one per line, and prints the probability for each next to the pack it was judged under.

Measured on 24 Sep 2026, thirteen sentences, of which eight reach Jev. The four everyday plans that
are not health promises scored **0.01, 0.01, 0.02 and 0.03**. The four promises about the patient's own
care scored **0.06, 0.15, 0.85 and 0.89**. So 0.8 keeps a 0.77 margin against the highest non-promise,
and the two positives under it — *"I will take the pram to the corner every afternoon"* and *"I will put
my feet up whenever I sit down"* — are genuine misses: Jev reads them as ordinary life rather than
care. That is the trade this floor makes on purpose. A missed promise costs nothing, the fact is simply
not stored as a `commitment`; a false one puts a promise in a patient's mouth and reads it back to them
a week later.

**The wording is what the number depends on, and it moved once already.** The first question asked only
whether the patient was *promising to do something themselves*, which is true of any first-person plan:
*"I will call my brother tonight"* scored 0.83 while a real promise scored 0.49, and no floor separates
those. Naming health, care and recovery in the question is what opened the gap. Re-run `make smoke-jev`
after touching `INSTRUCTIONS` or `CRITERIA` in `app/jev.py`, and read the gap off that output rather
than trusting the number here.

`STT_CONFIDENCE_FLOOR` is the one that needs calibrating on real calls. µ-law at 8 kHz scores lower
than clean audio across the board, so a floor tuned on a laptop microphone makes the agent read
every number back. Raise it only after listening to a take: the cost of it being too low is a longer
call, and the cost of it being too high is a wrong number stored as a fact.

`LANGUAGE` is the one worth leaving alone. It feeds `stream_url()` in
[`../app/stt.py`](../app/stt.py) and `transcribe()` in [`../app/analysis.py`](../app/analysis.py), but
nothing else: the packs, the TTS and the red-flag regexes are English, so setting `LANGUAGE=es` puts
the recogniser in Spanish while the agent keeps speaking English — and a real red flag stops matching
the guard. The project is English only, as [`ARCHITECTURE.md`](ARCHITECTURE.md) says.

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

> **Nothing here has been applied yet.** `constancia-voice.onrender.com` answers `404` with
> `x-render-routing: no-server`: no service, no database. This section is the runbook for when it
> is, and the deploy is row 1 of [`PENDINGS.md`](PENDINGS.md).

A multi-stage [`../Dockerfile`](../Dockerfile): a `node:24-slim` stage builds `web/dist`, then a `uv`
stage installs the Python deps, copies `app/`, `schema.sql`, `seed/` and the built front end, and runs
as a non-root user. One image, one service, one public URL — the API serves the pages.

[`../render.yaml`](../render.yaml) declares the Render service — `constancia-voice`, Docker runtime,
free plan, `healthCheckPath: /health` — **and the database**: `constancia-db`, free plan, Postgres 17, the same
major as `make db`. `DATABASE_URL` comes from it with `fromDatabase`, so there is no connection
string to copy. Nine entries stay `sync: false` and are typed into the dashboard — the eight required
variables plus `GEMINI_MODEL`, which is a pin rather than a credential; none of them is in the repo.

The container binds `${PORT:-8000}`; Render sets `PORT`. Local development uses 8001.

**The schema will apply itself at boot.** When the store is Postgres, the lifespan runs `schema.sql`
before serving (`app/main.py`) — it is idempotent end to end, so every boot after the first is a
no-op, and `tests/test_db.py` asserts exactly that. A fresh Render database will therefore come up
with its three tables and the `vector` extension already there. If the database is unreachable the
service
fails to start and the deploy goes red, which is the loud version of the problem: before this, the
health check passed and every screen with data returned `500`.

### The order

```bash
git push                      # 1. the Blueprint builds from the repo
                              # 2. New > Blueprint on Render, pick this repo, apply render.yaml
                              # 3. type the nine credentials into the service's Environment tab
                              # 4. PUBLIC_BASE_URL = the URL Render just assigned, then redeploy
make seed                     # 5. from your laptop, with .env pointing at the managed database
curl https://constancia-voice.onrender.com/health    # 6. from another network: {"store":"postgres","live":true}
```

The service is named `constancia-voice`, not `constancia`: the plain subdomain is held by an
unrelated application, and Render would have answered by appending a random suffix to the hostname —
which the endcard burns into the last frame of the video. Confirm in step 4 that the URL Render
assigned is the expected one before rendering the card.

**Leave `DEMO_PHONE` unset on Render.** The eight required variables make `/health` report
`live: true`, so
the deployed panel renders the two live buttons; with no demo phone they answer `400` instead of
dialling. That is the intended outcome for a public URL — the alternative is a stranger ringing your
phone. The scripted pair above them is the primary one and works with no phone at all.

Step 5 is the one that surprises people: `scripts/seed.py` needs **a full `.env`, not just
`DATABASE_URL`** — `MemoryStore()` builds `Settings`, which requires all eight credentials, and
`embed()` calls Gemini for every fact, so the key has to be a working one. Point `DATABASE_URL` at
the external connection string Render shows for the database and run it once.

### Two things about the free plan

- **The service sleeps after 15 minutes without traffic** and takes about a minute to come back, with
  a loading page in between. A judge opening a cold URL waits that minute. Either keep a ping every
  ten minutes from a free uptime service, or upgrade the instance for the judging window.
- **A free Postgres expires 30 days after it is created**, then has a 14-day grace period before
  Render deletes it. Created now it would outlive the deadline comfortably, but it is not a place to
  leave anything you want to keep.

## Checkpoints that need a person

Four things cannot be verified from a terminal alone, because someone has to answer a phone or click
in a dashboard. They are tracked in [`PLAN.md`](PLAN.md):

| | After | What it proves |
|---|---|---|
| C1 | Stage 1 | `make smoke` rings; a real call greets, asks the four questions in order, honours barge-in and says goodbye; the trace shows both sides. |
| C2 | Stage 2 | Three real calls back to back with no reset: the third opens on the knee, the 7/10 is superseded by the 4/10 in the store, and `memory=off` does not ask about the knee. The seed store is enough — the supersession is what C2 proves, not which store holds it. |
| C3 | Stage 3 | The panel during a live call: transcript, rail with the highlight, the chain, the chart. |
| C4 | Stage 4 | A public URL reachable from another network, the video, the deck. |

**Where each one stands:** C1 closed on live calls. C2 and C3 are open and close together during the
recording session — the three-call sequence is C2 and the panel that films it is C3, which is why
[`video-script.md`](video-script.md) puts the sequence before the final reset. C4 waits on the deploy.

[`../app/analysis.py`](../app/analysis.py) has met real recordings: C1 closed on live calls, and the
401 it answered the first time is why the mp3 is relayed through AssemblyAI's `/v2/upload` instead of
handed over by URL. Its pure functions are still tested against a canned response, and
`make smoke-analysis` is what re-checks the wire format by hand.

---

The commands themselves are in [`WORKING.md`](WORKING.md).
