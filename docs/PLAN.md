# constancia — implementation plan

Roadmap for building what `INTENT.md` specifies. Four stages, each ending in a checkpoint that needs a human (keys, a phone, a screen recording). Tick the boxes as stages land.

## Context

`INTENT.md` fixes the build order: **stage 1 is the voice loop end to end with a fixed prompt and no memory**, then memory, then the panel, then deploy and deliverables. The agent speaks Rioplatense Spanish to the patient; everything that lives in the repo (code, docs, commits) is in English; prompts and patient lines are content and stay in Spanish.

## Assumptions

- **No credentials exist locally** at the time of writing. Everything is developed and tested with no network (`ScriptedPatient` + scripted LLM + in-memory store). Live paths are exercised at each checkpoint once `.env` is filled.
- Tooling: `uv` with Python 3.12 (`uv venv -p 3.12`), no poetry. Node 24 + pnpm for the panel. Docker for a local Postgres.
- Models as of 2026-09-02: latest stable Flash is `gemini-3.8-flash`; `google-genai` 2.22.0, `client.models.generate_content` still works (docs lead with the Interactions API; `generate_content` is simpler). Embeddings: `gemini-embedding-001` at 1536 dims with L2 normalization per the spec; `gemini-embedding-2` normalizes by itself, decide with `models.list` on day 1 (the code always normalizes, which is harmless).
- STT in Spanish: `speech_model=universal-streaming-multilingual`, `language_codes=["es"]`, `encoding=pcm_mulaw`, `sample_rate=8000`. Audio goes from Twilio to AssemblyAI with a single `base64.b64decode`; no resampling. Raw `websockets` instead of the `assemblyai` SDK (simple JSON protocol, full asyncio control). Post-call: pre-recorded API with `entity_detection` + `sentiment_analysis` (`punctuate=true`), Spanish supported.
- TTS: ElevenLabs REST streaming `POST /v1/text-to-speech/{voice_id}/stream?output_format=ulaw_8000`, `model_id=eleven_flash_v2_5` (Spanish), via `httpx`; no SDK. `ulaw_8000` has no tier restriction.
- Local webhooks via **ngrok** (installed, needs `ngrok config add-authtoken`). Render in stage 4. Render free sleeps after 15 min: paid instance or external ping on judging day.
- A Twilio trial account is enough for the checkpoints (calls verified numbers only, prepends a trial message).
- `gh` has `german-massello` active and the remote belongs to `gmassello`: run `gh auth switch` before any `gh` operation on this repo. Nothing is committed without an explicit request.
- No comments in code except `ponytail:` markers on deliberate ceilings.

## Deviations from INTENT (annotate INTENT when each lands)

1. **The extractor receives every current fact with its id** (already loaded by `recall`, fewer than 50) instead of top-5 via pgvector: simpler and more accurate for deciding `supersedes`. pgvector stays for the professional's search in the panel.
2. **Speech Understanding does not feed the extractor**: the recording arrives by callback after hangup, and extraction runs at hangup on the live transcript. Entities and sentiment are stored in `calls.analysis jsonb` and shown in the panel and the trace.
3. **`patient_memories.value numeric`**: new column for the fact's number (pain 7/10) that feeds the weekly chart without parsing text.
4. **FastAPI serves the panel** (`panel/dist` as static files): one Render service, one public URL.
5. **Config with `pydantic-settings`** (spec) even though the loop design suggested `os.environ`: the spec wins.
6. **Facts carry a short `term`** (2-4 words, `patient_memories.term`) besides the full sentence: it is what feeds
   `keyterms_prompt` and what the panel shows. A whole fact sentence is a bad key term.
7. **`recall` runs before `greet`**, not after: the demo's money shot is the agent opening on the knee.
8. **Gemini's own schema conversion** is used for structured output (`response_schema=FactSet`): the SDK converts
   the Pydantic model, so hindsight's `clean_schema` (written for tool declarations) is not needed here.
9. **`app/analysis.py` and `MemoryStore.search()` moved to stage 3**: the first needs a real recording (C1 has not
   happened yet), the second has no reader until the panel. `calls.analysis` is not created until then.

## Checkpoints (need a human)

| # | After | What the human does | What must happen |
|---|---|---|---|
| C1 | Stage 1 | Fill `.env` (Gemini, AssemblyAI, Twilio SID/token/number, ElevenLabs key/voice), `ngrok config add-authtoken`, `ngrok http 8000`, answer the phone | `make smoke` rings; `make call PHONE=+54...`: greeting, 4 questions in order, barge-in, goodbye; `/calls/{id}/trace` shows both sides |
| C2 | Stage 2 | Create a Supabase project (or use `make db` locally), set `DATABASE_URL`, answer two calls | Call 1 from scratch; call 2 opens on the knee; 7/10 superseded by 4/10 in the DB; `memory=off` does not ask about the knee |
| C3 | Stage 3 | Open the panel during a call | Live transcript, rail with highlight, superseded chain, chart, replay with no keys |
| C4 | Stage 4 | Render account, deploy, recording session with the skill, upload the video, submit the deck on lablab | Public URL from another network; `video/reset.sh --check` all green; `demo.mp4` under 300 s; `SUBMISSION.md` with evidence on every row |

---

# Stage 1 — Voice loop (no memory)

- [x] done — offline path green (`make test`, `make demo`), Docker image boots and answers `/health`; live path waits on C1

### File layout

```
constancia/
  pyproject.toml          uv, python 3.12, exact versions (==), [dev] pytest, pytest-asyncio, ruff
  uv.lock
  Makefile                dev / test / lint / demo / call PHONE=... / smoke / smoke-stt / smoke-tts / models
  Dockerfile              ringdown's (uv, non-root, $PORT)
  render.yaml             web docker, plan free, healthCheckPath /health, envVars sync:false
  .env.example            every key with an empty value
  .gitignore              .env, .venv, __pycache__, video/out/, video/*.mov, runs/, panel/node_modules, panel/dist
  CLAUDE.md               hard rules: repo in English, exact versions, no secrets, tests without network
  HACKATHON.md            rules and criteria transcribed from INTENT §5
  SUBMISSION.md           table criterion | how we show it | where the judge sees it | status
  README.md               "The 30-second version" + how to run + Honest limits (grows per stage)
  docs/PLAN.md            this file
  app/
    __init__.py
    config.py             Settings (pydantic-settings) + cached get_settings(); E.164 validated
    main.py               FastAPI: lifespan validates secrets, /health, POST /calls, /voice, /voice/status,
                          /voice/recording, WS /media/{call_id}, GET /calls/{id}/trace (JSON)
    security.py           twilio_form (signature against PUBLIC_BASE_URL + path) — ported from ringdown
    telephony.py          place_call(): client.calls.create(record=True, recording_status_callback)
                          + TwiML <Connect><Stream>
    stt.py                AssemblyAI v3 asyncio client: connect(keyterms), feed(bytes), turns() async iter,
                          update_keyterms(), terminate()
    tts.py                ElevenLabs stream → async iterator of µ-law bytes
    llm.py                GeminiLLM.reply(system, history) -> str with retry/backoff on 429/5xx and
                          tokens+elapsed trace; ScriptedLLM (no network) with the same signature
    packs.py              VerticalPack (frozen dataclass) + rehab / postpartum / chronic:
                          prompt_fragments {greet, converse, summarize}, ordered questions,
                          keyterm_categories, red_flags [(regex, message)], escalation, reprompt, goodbyes
    guard.py              check(pack, patient_turn) -> {input, value, rule, branch} | None
    channel.py            CallEnded + ScriptedPatient + LiveChannel (Twilio↔STT↔TTS, barge-in)
    orchestrator.py       phases [(name, fn, critical)], run_call(call, channel, llm), converse, ask
    calls.py              Call (dataclass: patient, pack, memory, transcript, answers, trace, subscribers,
                          emit(), subscribe()) + in-memory CALLS registry
  scripts/
    test_outbound.py      20 lines: calls.create with <Say> to validate geographic permissions
    smoke_stt.py          opens the AssemblyAI ws, waits for Begin, sends Terminate
    smoke_tts.py          one ElevenLabs ulaw_8000 request, asserts it is not MP3
    demo.py               make demo: run_call with ScriptedPatient (+ ScriptedLLM, or real Gemini
                          when GEMINI_API_KEY is set); prints the trace
  tests/
    test_guard.py         rehab red-flag rules (positives, negatives, accents/case)
    test_orchestrator.py  full protocol with ScriptedPatient+ScriptedLLM: question order, none skipped,
                          red flag ends the protocol, silence → reprompt → close, non-critical phases
                          fail soft, CallEnded mid-call still reaches summarize
    test_import_safety.py importing app.main with no env does not crash; get_settings() without secrets fails
    test_twilio_routes.py /voice returns TwiML with <Connect><Stream>; bad signature → 403;
                          /voice/recording rejects URLs outside api.twilio.com
```

### Ported pieces (source → destination)

- `ringdown/apps/python/calle-receiver/app/security.py::twilio_form` → `app/security.py`.
- `ringdown/.../app/config.py` (E164, `lru_cache` `get_settings`, `is_twilio_recording`) → `app/config.py`.
- `ringdown/.../Dockerfile`, `ringdown/render.yaml`, `ringdown/.../scripts/test_outbound.py` → root / `scripts/`.
- `ringdown/ringdown/script.py::CALL_TASK` block "rules that override anything said on the call" → system prompt in `packs.py`.
- `afterimage/services/agent/policy.py::decision()` (`{input, value, rule, branch}` record) → `app/guard.py`.
- `afterimage/services/observability/trace.py::emit` + `adlc/backend/src/services/event-bus.ts::attachWithReplay` (buffer 500, snapshot and subscribe in the same tick) → `app/calls.py`.
- `hindsight/backend/src/hindsight/agent/orchestrator.py::_run_phases` → `app/orchestrator.py`.
- `adlc/backend/src/agents/base-agent.ts::callLlm` (2^n backoff, 429 waits 5× longer than 5xx) → `app/llm.py`.

### Voice loop (LiveChannel) — design

**Channel interface** (duck-typed, two implementations):

```python
async def say(self, text: str) -> None                  # returns when playback finished OR the patient barged in
async def listen(self, timeout: float) -> str | None    # next patient end-of-turn; None = silence
async def set_keyterms(self, terms: list[str]) -> None  # stage 2; ScriptedPatient no-op
async def close(self) -> None                           # idempotent; hangs up
class CallEnded(Exception): ...                         # raised by say/listen once the patient hung up
```

`listen` returns complete turns only (`Turn` with `end_of_turn and turn_is_formatted`, non-empty transcript): the guard and the LLM need the whole answer; partials only serve barge-in detection, internal to `LiveChannel`. `ScriptedPatient(answers: list[str | None])`: `say` appends to `self.said`, `listen` returns the next answer (`None` scripts silence).

**Asyncio tasks inside `WS /media/{call_id}`** (state: `stream_sid`, `started: Event`, `hung_up: Event`, `turns: Queue[str | None]` with `None` as hangup sentinel, `speaking: bool`, `barge: Event`, `mark_event: Event`, `tts_task`):

- `_twilio_reader`: `start` → `stream_sid`, `started.set()`. `media` → base64-decode and buffer; every 800 bytes (5 × 20 ms frames = 100 ms) send one binary frame to AssemblyAI. `mark` → `mark_event.set()` (one outstanding mark at a time). `stop`/disconnect → `hung_up.set()` + sentinel.
- `_aai_reader`: `Turn` with transcript: if `speaking` and `len(words) >= BARGE_MIN_WORDS` (default 2; 0 disables) → `barge.set()`; if `end_of_turn and turn_is_formatted` → `turns.put_nowait(transcript)`. `Termination`/close → `hung_up` + sentinel.
- `_stream_tts(text)`: POST ElevenLabs stream `ulaw_8000`, each chunk → base64 `media` to Twilio; then `mark`; wait for `mark_event` with timeout `bytes/8000 + 2` s (µ-law is exactly 8000 B/s).

`say()` races `tts_task` against `barge.wait()`: if barge wins → cancel TTS, **`gather` it until it has unwound** (a single writer on the Twilio socket), send `clear`, emit `agent_turn interrupted=True`. The interrupting turn lands in `turns` and the next `listen` takes it as the answer. `turns` is drained at the start of `say` (stale backchannels); never after a barge-in.

`start()`: connect to AssemblyAI (`Authorization: <key>`, no Bearer; `language_codes` and `keyterms_prompt` as `json.dumps` + urlencode), spawn both readers, wait for `started` with a 10 s timeout. `close()`: cancel TTS, `hung_up.set()`, close the Twilio ws (Twilio hangs up), `Terminate` to AssemblyAI and close, cancel readers with `gather(return_exceptions=True)`.

**Startup**: `POST /calls {patient_id, memory}` creates a `Call` in `CALLS` and dials with `calls.create(url=PUBLIC_BASE_URL/voice?call_id=..., record=True, recording_status_callback=...)`. `POST /voice` answers `<Connect><Stream url="wss://{host}/media/{call_id}">`. The ws handler looks up the `Call`, `accept`, `LiveChannel.start()`, `run_call(call, channel, GeminiLLM())`, `finally: channel.close()`. A patient hangup surfaces as `CallEnded` on the next `say`/`listen`; `converse` catches it, emits a warning, and the pipeline continues into `extract/store/summarize`. Normal end: `converse` says goodbye (waits for the mark), `run_call` closes the channel before `extract` so the patient is not left on a silent line.

**`converse`** (code decides, the LLM phrases):

```
for q in pack.questions:                       # Question(key, goal)
    text = phrase(llm, call, "Preguntá sobre: " + q.goal)   # emits llm {tokens, elapsed_ms}
    ans  = ask(channel, call, text)            # say → listen(SILENCE_S) → pack.reprompt → listen → None
    if ans is None: say(pack.goodbye_silent); return
    hit = guard(pack, ans)                     # {input, value, rule, branch} or None
    if hit: emit guard_hit; say(phrase(llm, pack.escalation)); call.escalated = hit; return
    call.answers[q.key] = ans
say(pack.goodbye)
```

**LLM per turn**: full text, then TTS (one `generate_content` call, `max_output_tokens≈80`, `temperature 0.4`). `ponytail:` ceiling: ~1–1.5 s of silence between end of turn and first audio; the upgrade is `generate_content_stream` split on sentences into sequential `_stream_tts` calls inside the same `tts_task`.

**Likely failures on the first live call and mitigation**:
1. `connected` arrives but never `start` → 10 s timeout; almost always the `wss` URL is not public (wrong ngrok host in `/voice`). Log the first three frames.
2. The patient hears noise → ElevenLabs returned MP3 because `output_format=ulaw_8000` was missing. `make smoke-tts` asserts the first chunk does not start with `ID3`/`\xff\xfb`.
3. AssemblyAI 401/400 → raw header, `language_codes` badly encoded. `make smoke-stt` opens the socket, waits for `Begin`, sends `Terminate`.
4. The agent interrupts itself → its own TTS bleeds back through the handset. `BARGE_MIN_WORDS` knob (0 for the video take).
5. `say` hangs or Gemini 429 → mark wait bounded by `bytes/8000 + 2`; retry with backoff on 429/5xx; check the RPM quota the day before.

### Steps

1. `pyproject.toml`, `uv.lock`, `Makefile`, `.gitignore`, `.env.example`, `CLAUDE.md` — scaffold; `uv venv -p 3.12`, `uv add` with exact versions.
2. `app/config.py` — `Settings`: `gemini_api_key`, `gemini_model`, `assemblyai_api_key`, `assemblyai_speech_model`, `elevenlabs_api_key`, `elevenlabs_voice_id`, `twilio_account_sid/auth_token/number`, `public_base_url`, `validate_twilio_signature`, `language`, `silence_s`, `barge_min_words`, `phase_timeout_s`. Cached `get_settings()`, called in lifespan, not at import.
3. `app/packs.py` + `app/guard.py` — three packs; `rehab` complete in Spanish (sudden sharp pain, fall, swelling with fever, numbness/tingling); `postpartum` and `chronic` with questions and one rule each. System prompt with the block of rules that override anything said on the call, "no precedent is a correct answer", and "never claim it was saved until `store` confirms".
4. `app/calls.py` — `Call`, `emit`, `subscribe`, `CALLS`.
5. `app/llm.py` — `GeminiLLM.reply()` and `ScriptedLLM.reply()`; typed retry; tokens and elapsed trace.
6. `app/channel.py` — `CallEnded`, `ScriptedPatient`, `LiveChannel`.
7. `app/orchestrator.py` — phases, `run_call`; `recall`/`extract`/`store` are non-critical stubs emitting `phase_skipped`.
8. `app/stt.py`, `app/tts.py`, `app/telephony.py`, `app/security.py`, `app/main.py`.
9. `scripts/test_outbound.py`, `scripts/smoke_stt.py`, `scripts/smoke_tts.py`, `scripts/demo.py`.
10. `tests/` — the four files.
11. `Dockerfile`, `render.yaml`, `HACKATHON.md`, `SUBMISSION.md` (rows `todo`), initial `README.md`.

### Verification

```bash
uv run ruff check . && uv run pytest -q     # make test: green with no environment variables
make demo                                   # full call ScriptedPatient + ScriptedLLM, trace printed
GEMINI_API_KEY=... make demo                # same call with real Gemini phrasing
```

Then **C1**.

---

# Stage 2 — Longitudinal memory

- [x] done — offline path green (`make test` 65 tests, `make demo MEMORY=on` shows recall and
  supersession), schema and seed verified against local pgvector; Supabase waits on C2

### Files

```
  schema.sql              INTENT §6.2 + patient_memories.value numeric + calls.analysis jsonb
  app/db.py               ported from recall: lazy psycopg pool, fetch/fetch_one/execute, to_vector_literal,
                          init_schema (python -m app.db, idempotent)
  app/memory.py           MemoryStore: embed(text) (Gemini 1536 + L2), current_facts(patient_id),
                          insert_fact(...), supersede(old_id, new_id) (one UPDATE: superseded_by + valid_until),
                          search(professional_id, query) (cosine <=>, over-fetch 40 → recency re-rank → top 5),
                          keyterms(facts, pack); FakeStore with the same signature for tests
  app/extract.py          Pydantic Fact {fact, category, value, quote, turn_id, confidence, supersedes, valid_until}
                          and FactSet; clean_schema (inline $ref, drop title, uppercase type) ported from hindsight;
                          complete_structured(system, transcript, FactSet) with response_schema and ×3 retry
                          feeding back the ValidationError; ground(fact, transcript): quote inside turn
                          turn_id and the turn is the patient's (ported from ringdown ground_span)
  app/analysis.py         post-call: recording_url → AssemblyAI pre-recorded (entity_detection,
                          sentiment_analysis, punctuate, language es) → calls.analysis; BackgroundTask
  app/orchestrator.py     recall: current_facts → system prompt block (newest first, with reported_at)
                          + channel.set_keyterms; extract: complete_structured with current facts + ids;
                          store: embed + insert + supersede; summarize: weekly summary from the fact set;
                          memory=False skips recall and store
  app/queries.py          (born here, grows in stage 3) chain(patient_id), weekly(patient_id)
  seed/patients.json      Ana (rehab), week-1 facts with age_days=7: right knee 7/10 on stairs,
                          skipped exercises twice; one historical red_flag fact; call 1 with transcript
  scripts/seed.py         deterministic, idempotent (by external key), no randomness
  tests/test_extract.py   grounding (quote from an agent turn → rejected), clean_schema (ported from
                          test_gemini_schema), retry on ValidationError with a fake LLM
  tests/test_memory.py    FakeStore: supersede retires the old one, current_facts no longer returns it, keyterms
                          by category; tests against real Postgres marked integration (skipped without DATABASE_URL)
  tests/test_orchestrator.py  + memory=off vs on: call 2's prompt contains "rodilla" only with memory
  docker-compose.yml      pgvector/pgvector:pg17 for local `make db`
```

### Steps

1. `schema.sql`, `app/db.py`, `docker-compose.yml`, `make db` / `make schema`.
2. `app/memory.py` with `MemoryStore` and `FakeStore`.
3. `app/extract.py` and its tests.
4. `app/orchestrator.py`: real phases; `run_call(call, channel, llm, store)`.
5. ~~`app/analysis.py` + `/voice/recording` triggers the analysis in the background.~~ moved to stage 3.
6. `seed/patients.json`, `scripts/seed.py`, `make seed`.
7. `POST /calls` accepts `memory: bool`; `GET /patients/{id}/facts` (chain) to verify at C2 without the panel.
8. `README.md` Honest limits: turn latency, no auth, single worker.

### Verification

```bash
make test                                        # no network: FakeStore
DATABASE_URL=... make schema && make seed && uv run pytest -m integration
make demo MEMORY=on                              # week-2 ScriptedPatient over the seed: recall shows the knee
```

Then **C2**.

---

# Stage 3 — Professional's panel and replay

- [ ] done

### Files

```
  app/queries.py          the single query module: patients(), patient(id), calls(patient_id),
                          chain(patient_id) (facts with superseded_by resolved), weekly(patient_id)
                          (value per week for category symptom), keyterms_used(call_id), red_flags(patient_id)
  app/main.py             GET /patients, /patients/{id}, /patients/{id}/calls, /patients/{id}/chain,
                          /patients/{id}/weekly, /calls/{id}/events (SSE: buffer replay + live,
                          keep-alive every 15 s), /calls/{id}/trace (JSON or HTML by Accept),
                          POST /calls {patient_id, memory, mode: live|scripted|replay};
                          StaticFiles at / serving panel/dist
  app/replay.py           replays seed/replay/*.json (events with relative ts) through the same bus,
                          honouring timings; `scripted` runs ScriptedPatient + Gemini with no phone
  seed/replay/week1.json, week2-off.json, week2-on.json   recorded from real calls at C2
  panel/                  Vite + React 19 + TypeScript, no UI or charting libraries
    src/api.ts            fetch + EventSource with reconnect and backoff
    src/App.tsx           patient list → patient view
    src/PatientView.tsx   header, "Call now" button (memory on/off, mode), calls
    src/LiveCall.tsx      live transcript (SSE) + ActivityRail
    src/ActivityRail.tsx  every turn and every fact, verbatim; 4 s highlight on fact_stored / fact_superseded
    src/FactChain.tsx     current → superseded chain, with quote and turn_id
    src/WeeklyChart.tsx   divs with proportional height, value printed (ported from SalesChart)
    src/Keyterms.tsx      the keyterms that fed the STT on that call
  tests/test_queries.py   with FakeStore/seed: weekly and chain deterministic
  tests/test_sse.py       buffer replay on late connect; keep-alive
```

### Steps

1. `app/queries.py` + endpoints + tests.
2. SSE with replay buffer (`Call.subscribe()` already exists).
3. `app/replay.py` and recorded fixtures (`GET /calls/{id}/export` to dump them at C2).
4. Panel: `pnpm create vite` scaffold, components, dev proxy to `localhost:8000`; `make panel` builds to `panel/dist`.
5. `[!WARNING]` about no auth in README.

### Verification

```bash
make test && cd panel && pnpm test && pnpm build
make dev                       # open http://localhost:8000, Call now mode=replay: the call shows with no keys
```

Then **C3**.

---

# Stage 4 — Deploy, video and deliverables

- [ ] done

### Files

```
  Dockerfile              multi-stage: node build of panel/ → uv python 3.12 image
  render.yaml             full envVars, healthCheckPath /health
  video/narration.tsv     the 7 beats of INTENT §9 (280 s), columns beat/gap/caption/speak
  video/reset.sh          --check: seed patient exists, week-1 facts present, no call in flight,
                          no facts from previous takes (call_id outside the seed), Gemini/AssemblyAI quota
                          checked by hand; without --check: deletes what the previous take left behind
  docs/video-script.md    numbered shot list, money shots 🎯 (beats 3 and 5), exact patient lines
                          per call, "what can come out differently", opening and closing URLs
  docs/deck.md            slides (problem, product, demo, architecture, business, Law 25.326, team)
  video/out/endcard.png   name, URL, repo, MIT via ffmpeg drawtext
  SUBMISSION.md           evidence on every row (path, URL or video timestamp)
  README.md               final: 30-second version, criteria table, Honest limits, how to run, video
```

### Steps

1. Multi-stage Dockerfile, `make deploy` (push + Render auto-deploy), Supabase `DATABASE_URL` on Render, `PUBLIC_BASE_URL` = Render URL, `make seed` against Supabase.
2. `video/reset.sh`, `docs/video-script.md`, `video/narration.tsv`; `build-audio.sh` and listen to the narration.
3. Recording session with the `personal-record-video` skill (1280x800 window, mic off, phone off camera); `fit-to-audio.py`, `build-video.sh`, `MAX_SECONDS=300`.
4. `docs/deck.md`, endcard, `SUBMISSION.md`, `README.md`, `HACKATHON.md` reviewed.
5. Annotate the deviations above in `INTENT.md`.

### Verification

```bash
curl https://<render-url>/health                 # from another network
bash video/reset.sh --check                      # all green
VIDEO_DIR=$PWD/video bash .../build-video.sh video/out/raw-fitted.mov   # demo.mp4 under 300 s
```

Then **C4** and submission on lablab (human).

---

## Out of scope (all stages)

- Panel auth and multi-tenancy; weekly scheduler; hash-chained audit log; memory as tools; AssemblyAI feedback doc; real legal compliance; device integration (all per INTENT §12).
- Sentence-streamed LLM into TTS (ceiling marked).
- Vercel for the panel (FastAPI serves it).
- Commits and pushes without an explicit request.
