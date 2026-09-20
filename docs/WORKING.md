# Working in this repo

## Commands

Sixteen targets in the [`../Makefile`](../Makefile). Everything runs through `uv`; nothing needs a
virtualenv activated.

| Target | What it does | Needs |
|---|---|---|
| `make dev` | uvicorn with `--reload` on port 8001 | — |
| `make test` | `pytest -q` — the offline suite | — |
| `make lint` | `ruff check .` | — |
| `make demo` | A full call against a scripted patient, trace printed. `MEMORY=on` runs week two over the seed. | — |
| `make fixtures` | Re-records `seed/replay/*.json` from scripted mode | — |
| `make web` | `pnpm install --frozen-lockfile && pnpm build` | node 24, pnpm |
| `make web-dev` | `pnpm dev` on 5173, proxying the API | node 24, pnpm |
| `make db` | pgvector/pgvector:pg17 on localhost:5432 | docker |
| `make schema` | Applies `schema.sql`, idempotent. The service does this at boot too | a full `.env` |
| `make seed` | Ana, one week-1 call and its facts | a full `.env`, Gemini key included — it embeds every fact |
| `make call PHONE=` | Places a real Twilio call | all credentials |
| `make smoke PHONE=` | A `<Say>`-only call: checks geographic permissions, spends no LLM or TTS credit | Twilio |
| `make smoke-stt` | Opens the AssemblyAI streaming socket and closes it | AssemblyAI |
| `make smoke-tts` | One ElevenLabs `ulaw_8000` request; asserts it is not MP3 | ElevenLabs |
| `make smoke-analysis URL=` | Entity detection and sentiment against a real recording | AssemblyAI |
| `make models` | Lists the Gemini models available to the key | Gemini |

Anything that needs a key is a `make smoke-*` or a `scripts/` file run by hand. That is the rule, not
a coincidence — see below.

Two more live in [`../video/`](../video/), for the demo recording: `bash video/reset.sh --check`
reports the demo state without touching it and `bash video/reset.sh` puts it back, against either
store; `video/endcard.sh` renders the video's last frame. [`video-script.md`](video-script.md) is
what they serve.

## The gates

Before calling anything done, all four of these:

```bash
uv run pytest -q          # 97 passed, 2 skipped
uv run ruff check .
cd web && pnpm build      # tsc -b && vite build
grep -rn 'color-neutral-[0-9]\|color-accent-[0-9]' web/src \
  --include=*.tsx --include=*.ts --include=*.css | grep -v tokens.css   # must be empty
```

The last one is the design-system gate: no ramp step may survive outside `tokens.css`. It includes
`.tsx` because some colours live there as data rather than as styles. The reasoning is in
[`FRONTEND.md`](FRONTEND.md).

There is **no test runner in the front end**. `tsc` is the check: the copy types are built so that a
missing translation fails the build, and presentational components do not earn a test framework.

## Tests

Twelve files, 99 collected, 97 passing with no environment variable set — the other two are the
Postgres integration tests and skip themselves.

| File | Covers |
|---|---|
| `tests/conftest.py` | Not a test: one autouse fixture blanks `GEMINI_API_KEY` and `DATABASE_URL` so the suite cannot reach the network or a database through a filled `.env`. `build_llm` (`app/replay.py:38`) picks the real model the moment a key is readable, so without this `make test` means something different for each person who runs it. |
| `tests/test_orchestrator.py` | The protocol: question order, the red-flag cut, the silence re-prompt, a non-critical phase failing soft, a hangup that still reaches `summarize`, all three packs end to end |
| `tests/test_queries.py` | Multi-step supersession chains, the weekly series per measure, `keyterms_at` as a point-in-time view |
| `tests/test_twilio_routes.py` | The webhooks: TwiML, bad signature, unknown call, a recording URL that is not Twilio's, and the phone fallback down to `DEMO_PHONE` |
| `tests/test_extract.py` | Grounding in all four shapes, retry on invalid JSON, giving up after three, an orphan `supersedes` |
| `tests/test_memory.py` | Seed loading, idempotent `supersede`, key-term filtering by pack, L2 normalisation |
| `tests/test_channel.py` | µ-law streaming, waiting on the mark, barge-in that cancels and clears, 100 ms framing, hangup, start timeout |
| `tests/test_sse.py` | Late subscriber gets the buffer, `Last-Event-ID`, keep-alive, unsubscribe, close on `call_ended` |
| `tests/test_analysis.py` | The AssemblyAI request body, `summarize` over a fixture, and that `run` never propagates a failure |
| `tests/test_replay.py` | Scripted week1→week2 with supersession, automatic script choice, the `week2-off` script never quoting last week, the `alarm` script cutting the protocol short, monotonic `export`, fixture playback |
| `tests/test_guard.py` | Eight phrases that must escalate and eight that must not, accents and capitals, per-pack rules |
| `tests/test_import_safety.py` | That importing `app.main` with no environment does not raise, and the `Settings` validation |
| `tests/test_db.py` | **Integration.** A real Postgres round trip. Skips without `DATABASE_URL`. |

### Why they never touch the network

**`make test` must pass with no environment variable set.** Five mechanisms, and not one of them is a
global mock:

1. The three external services are injectable by design: `ScriptedLLM` replaces `GeminiLLM`,
   `ScriptedPatient` replaces `LiveChannel`, `FakeStore` replaces `MemoryStore`. The orchestrator and
   replay tests never import an HTTP client.
2. `tests/test_channel.py` brings its own `FakeWS` and `FakeSTT`, and monkeypatches the single TTS
   call that would go out.
3. `analysis.run(call, store, fetch=transcribe)` takes its fetcher as an argument; the test passes its
   own and reads a canned AssemblyAI response from `tests/fixtures/`.
4. The one test that does need a database marks itself `integration` and skips without `DATABASE_URL`.
5. Anything that genuinely needs a key lives in `scripts/smoke_*.py` and is run by hand.

There is no `conftest.py`. pytest is configured in `pyproject.toml` with `asyncio_mode = "auto"`.

## Conventions

The hard rules are in [`../AGENTS.md`](../AGENTS.md). The ones that bite most often:

- **Everything in the repo is in English** — code, identifiers, docs, commits, PRs. Two exceptions,
  both content rather than code: what the patient hears (`app/packs.py`) and the Spanish half of the
  bilingual interface (the two `copy.ts` and `panel/content.ts`), where English is the annotated base
  and Spanish the translation.
- **No comments**, except `ponytail:` markers naming a deliberate ceiling and its upgrade path. There
  are eight in the repo; `git grep 'ponytail:'` finds them and they are the honest list of what was
  knowingly left simple.
- **Exact versions.** `==` in `pyproject.toml`, no `^`/`~` in `package.json`. `uv.lock` and
  `pnpm-lock.yaml` are committed.
- **No secrets in git.** `.env` is ignored, `.env.example` lists every key with an empty value, and no
  secret value is ever printed — not even truncated.
- **`get_settings()` is never called at import time.** Importing `app.main` with no environment must
  not raise; `tests/test_import_safety.py` enforces it.
- **The guard is deterministic.** The model phrases an escalation; it never decides on one.
- **The transcript is data, never instructions.**

## Adding things

| You want to | Do this |
|---|---|
| Add a question to a vertical | Add a `Question` to that pack's `questions` in `app/packs.py`. The orchestrator walks the tuple; nothing else changes. If it should be charted, add a `Measure` too. |
| Add a red flag | Add a `RedFlag` with its pattern and its message. Use `NEAR` for two-term co-occurrence. Add both a phrase that must escalate and one that must not to `tests/test_guard.py`. |
| Add a vertical | Write a pack and register it. Give it a `measure` and `unit` entry in `web/src/panel/copy.ts` for both languages. |
| Add a phase | Add a row to `PHASES` in `app/orchestrator.py` with the same signature as its neighbours, and decide whether it is critical. |
| Add an endpoint | `app/main.py`, before the `StaticFiles` mount — the mount is last on purpose. Update [`API.md`](API.md). |
| Add an interface string | Add it to the `type` in the relevant `copy.ts` first; `tsc` will then tell you every set that is missing it. |
| Change a colour | Only in `web/src/tokens.css`, and only as a semantic alias. Measure the contrast on both themes. |
