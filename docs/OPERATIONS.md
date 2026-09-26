# Running and deploying

## Three paths

The service degrades on purpose. Pick the shallowest one that shows what you need.

### 1. No keys at all

```bash
uv sync
make test          # 319 tests, no network and no database
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

`JEV_FLOOR` is measured, not chosen, and the measurement is a command rather than a count done by
hand. `make smoke-jev` posts the thirteen sentences the deterministic rules would face — five it takes
by vocabulary and eight it rejects and hands to Jev — prints the probability for each next to the pack
it was judged under, and writes
[`../scripts/jev-measured.json`](../scripts/jev-measured.json) with every probability, the summary,
and a hash of the question wording that produced them. Each sentence carries its expected answer as
**data** in `scripts/smoke_jev.py`, so recall, precision and the margin come out of the run; before
that they were a comment in prose and a person counting columns.

**Measured 25 Sep 2026, wording `117b8a3c18ac`: recall 0.50, precision 1.00, margin 0.78.** The four
everyday plans scored 0.01, 0.01, 0.02 and 0.02; the four promises about the patient's own care scored
0.06, 0.50, 0.96 and 0.97. So 0.8 sits 0.78 above the highest non-promise, and the two positives under
it — *"I will take the pram to the corner every afternoon"* and *"I will put my feet up whenever I sit
down"* — are the misses. That is the trade this floor makes on purpose. A missed promise costs
nothing, the fact is simply not stored as a `commitment`; a false one puts a promise in a patient's
mouth and reads it back to them a week later.

**The wording is what the number depends on, and it has moved twice.** The first question asked only
whether the patient was *promising to do something themselves*, which is true of any first-person plan:
*"I will call my brother tonight"* scored 0.83 while a real promise scored 0.49, and no floor separates
those. Naming health, care and recovery in the question is what opened the gap, and that wording ran
until 25 Sep at recall 0.50, precision 1.00, margin 0.77 — everyday plans at 0.01–0.03 and promises at
0.06, 0.15, 0.85, 0.89.

The wording in place now says three things the old one did not: that an **ordinary** action counts when
it is done for the recovery, that **following the professional's advice still counts** — the old text
excluded "what someone else told them to do", which is what half of physiotherapy is — and it names
what does not count by its own vocabulary (work, errands, seeing people, entertainment) instead of by
the absence of health. It did not move recall, which stays at 0.50 with the floor where it is, but it
moved everything around it: *"I will put my feet up whenever I sit down"* went from 0.15 to 0.50, the
two it already caught went from 0.85 and 0.89 to 0.96 and 0.97, and the best everyday plan fell from
0.03 to 0.02. The classifier separates better; the floor is what still excludes the near miss.

Two things worth knowing before the next attempt. **The model is not deterministic**: the same
sentence under the same wording scored 0.47, 0.50 and 0.56 across three runs, so a single run resolves
about ±0.05 and a change smaller than that is noise. And **the gateway rate-limits**: a run of eight
requests in a row can come back `429 rate_limit_exceeded`, which `app/jev.py` turns into the same
`None` as any other failure — the vocabulary decides alone and nothing on the call breaks.

**The label on the worst miss was questioned and it stands.** *"I will take the pram to the corner
every afternoon"* scored 0.06, 0.05 and 0.10 under three different wordings, and nothing in the
sentence itself says it is about her body, so the obvious move was to relabel it `EVERYDAY` and watch
recall jump to 0.67. It is not the right move, for two reasons that are testable rather than
editorial.

The action in it is **walking**, and walking is already a promise by this system's own deterministic
vocabulary: *"I will walk to the corner every afternoon"* scores 0.90 with no key and no network,
because `walk` is in `GENERIC_ACTION`. What the pram wording lacks is the verb, not the clinical
content — calling it an everyday plan would contradict a rule the code applies on every call.

And it cannot be rescued by widening the enumeration either. Appending `pram|pushchair|buggy` to the
postpartum pack's `actions` does catch it, at 0.90 — and it also scores *"I will buy a pram this
weekend"* and *"I am going to sell the pram next week"* at **0.90 each**, which are errands. `actions`
enumerates actions; `pram` is an object, and an object in an action list manufactures false positives
in a place where a false promise is the expensive kind of error.

So the sentence keeps its label and stays a miss, and what it measures is the **shape** of what the
second opinion buys. Jev rescues a promise whose action is named in the sentence — *keep the
stockings on*, *keep the wound dry*, 0.96 and 0.97. It does not rescue one where the action is only
implied by an object (the pram, 0.06) or worded as a condition rather than an action (*"whenever I sit
down"*, 0.50). Recall 0.50 is the honest figure for a sample made of the hard half on purpose.

**The floor has room and it is deliberately not spent.** At 0.8 the feet-up promise is dropped at
0.50; the best everyday plan is 0.02, so a floor of 0.5 would keep 0.48 of margin and take recall to
0.75. It stays at 0.8: four negatives is not a calibration set, the model resolves to about ±0.05 so
that 0.50 sits on the boundary of its own noise, and Jev's README asks for calibration against your
own data before its numbers are trusted as thresholds. The headroom is recorded so a later run with
more sentences knows where to look first.

Re-run `make smoke-jev` after touching `INSTRUCTIONS` or `CRITERIA` in `app/jev.py`, and read the gap
off `scripts/jev-measured.json` rather than trusting the numbers here.

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

> **Applied on 25 Sep 2026.** `https://constancia-voice.onrender.com` answers `/health` with
> `{"status":"ok","calls":0,"store":"postgres","live":true,"dialable":false}`, and `/patients` serves
> the seeded Ana. This section is the runbook that was followed, and the one to follow again.

A multi-stage [`../Dockerfile`](../Dockerfile): a `node:24-slim` stage builds `web/dist`, then a `uv`
stage installs the Python deps, copies `app/`, `schema.sql`, `seed/` and the built front end, and runs
as a non-root user. One image, one service, one public URL — the API serves the pages.

[`../render.yaml`](../render.yaml) declares the Render service — `constancia-voice`, Docker runtime,
free plan, `healthCheckPath: /health` — **and the database**: `constancia-db`, free plan, Postgres 17, the same
major as `make db`. `DATABASE_URL` comes from it with `fromDatabase`, so there is no connection
string to copy. Nine entries stay `sync: false` and are typed into the dashboard — the eight required
variables plus `AI_GATEWAY_API_KEY`; none of them is in the repo.

**Two decisions about that list, because a blank field is not the same as an absent one.** A variable
declared `sync: false` and left empty arrives as an empty string, and an empty string beats the
default in [`../app/config.py`](../app/config.py); what Render does with a field you skip is not
documented either way. So the model pins — `GEMINI_MODEL`, `GEMINI_EMBEDDING_MODEL`,
`ASSEMBLYAI_SPEECH_MODEL`, `ELEVENLABS_MODEL` — are **not declared at all**: they are defaulted in
`config.py`, that is where they are decided, and a second copy in the Blueprint could only disagree
with it. `AI_GATEWAY_API_KEY` is the opposite case and is declared even though it is optional: left
out, the deployed service silently loses the second opinion behind the promise rules, so every
sentence the action vocabulary rejects is dropped and the public URL behaves differently from a local
run with a full `.env`. Blank is a safe value for it — `config.py` defaults it to `""` and
[`../app/jev.py`](../app/jev.py) turns a missing key into the vocabulary deciding alone — so the
choice of whether the deployment gets Jev is made by typing the key or not, in one place, rather than
by forgetting it.

The container binds `${PORT:-8000}`; Render sets `PORT`. Local development uses 8001.

**The image was built and run before any of this was applied**, which is the cheap way to find a
broken `COPY` or a lockfile that does not resolve — a red build on Render costs a dashboard round
trip, and this costs one command:

```bash
docker build -t constancia:local .
docker run --rm -p 8010:8000 constancia:local          # no environment at all
curl -s localhost:8010/health                          # {"store":"seed","live":false,"dialable":false}
curl -s localhost:8010/ | grep -o '<title>[^<]*</title>'
```

Measured 25 Sep: nineteen steps green, **501 MB**, and with no environment set the container answers
`/health` on the seed store and serves both pages' own titles — so `web/dist` lands where `WEB_DIST`
looks for it and the non-root user can read it. One caveat worth writing down: on an arm64 laptop,
`docker build --platform linux/amd64` — Render's architecture — **fails under emulation**, and not
because of anything in the repo. pnpm's Rust binary panics inside qemu (*"unexpected error when
polling the I/O driver"*) at `pnpm install`. Build natively to check the Dockerfile; the architecture
itself is only exercised on Render, where `uv.lock` pins the same versions for every platform.

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
                              # 3. type the nine credentials into the Blueprint form
                              # 4. PUBLIC_BASE_URL = the URL Render just assigned, then redeploy
make seed                     # 5. from your laptop, with .env pointing at the managed database
curl https://constancia-voice.onrender.com/health    # 6. from another network: {"store":"postgres","live":true}
```

**Step 3 happens once, in the form.** A `sync: false` value is prompted while the Blueprint is being
created and nowhere else; afterwards the same nine live in the service's *Environment* tab, which is
also where step 4 is edited — and saving there triggers a redeploy on its own.

**Step 5 needs the external connection string, and step 5 is not finished until it is gone again.**
`fromDatabase` wires `DATABASE_URL` inside Render, so there is nothing to copy for the service; a
seed run from a laptop is outside that network and needs the **External Database URL** on the
database's *Info* page — the *Internal* one only resolves from inside Render. Paste it into `.env`,
run `make seed`, then **blank it again**: the recording session runs `make take`, and
[`../video/reset.sh`](../video/reset.sh) would wipe the database that was just seeded. Keeping the
string parked on a commented line below it costs nothing and makes the next seed a copy rather than
a dashboard trip.

The service is named `constancia-voice`, not `constancia`: the plain subdomain is held by an
unrelated application, and Render would have answered by appending a random suffix to the hostname —
which the endcard would burn into the last frame of the video. Confirm in step 4 that the URL Render
assigned is the expected one, then re-render the card with it: `PUBLIC_URL=<hostname> bash
video/endcard.sh`. Until then the card names no URL at all — the script defaults to empty and drops
the line, so the address on the last frame is the GitHub repo, which works.

**Leave `DEMO_PHONE` unset on Render, and that is what hides the dial buttons.** `/health` reports
two different things: `live`, which says the eight credentials validate, and **`dialable`**, which
says this instance also has a demo number of its own. The panel offers the two *Real phone* buttons
only when `dialable` is true, so a public deployment with no `DEMO_PHONE` does not render them at
all. It used to render them and answer `400` on a click — a stranger could not ring your phone, but a
judge got two dead buttons and the safety depended on remembering not to set a variable. Now the
variable is the switch and the UI obeys it. The scripted pair above them is the primary one and works
with no phone at all.

The gate is `tests/test_import_safety.py`, parametrised on the two states: with the eight
credentials and `DEMO_PHONE` empty, `dialable` is `false` while `live` is `true`; with a number, both
are `true`. The sidebar says which of the three states it is in — `no keys`, `no demo number`,
`ready`.

**It is a UI gate, not a lock.** `POST /calls` with `mode=live` and an explicit `phone` still dials
from a deployed instance that has credentials, because there is no authentication anywhere — which
the README says in its own warning. What `dialable` removes is the accidental case: a button on a
public page, and a stranger who presses it.

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
