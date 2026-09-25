# Working in this repo

## Commands

Nineteen targets in the [`../Makefile`](../Makefile). Everything runs through `uv`; nothing needs a
virtualenv activated.

| Target | What it does | Needs |
|---|---|---|
| `make dev` | uvicorn with `--reload` on port 8001 | — |
| `make take` | uvicorn without `--reload`, for a recording that a file save must not restart | — |
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
| `make smoke-call PHONE=` | A full call through the live channel, driven from the shell | all credentials |
| `make smoke-analysis URL=` | Entity detection, sentiment and key phrases against a real recording | AssemblyAI |
| `make smoke-keyphrases URL=` | Transcribes the same recording twice, with and without `auto_highlights`, and prints every phrase with its rank and count, marking the ones the fact vocabulary did not already hold. Writes `scripts/keyphrases-measured.json`, which is what decides whether the phrases keep feeding the next call's `keyterms_prompt` | AssemblyAI |
| `make smoke-jev` | Asks Jev the promise question about the eight sentences the vocabulary rejects, out of a labelled sample of thirteen, and prints the probability, the HTTP status and whether each one was rescued, then recall, precision and the margin. Writes `scripts/jev-measured.json`. The only way a 403, a 429 or a 503 becomes visible, because `app/jev.py` swallows them all | AI Gateway |
| `make models` | Lists the Gemini models available to the key | Gemini |

Anything that needs a key is a `make smoke-*` or a `scripts/` file run by hand. That is the rule, not
a coincidence — see below.

The four lines that are not targets, because they take an argument or belong to another tool:

```bash
uv sync                                     # install; there is no virtualenv to activate
uv run pytest tests/test_guard.py::test_red_flags_fire      # one test, the 90% case
uv run pytest -k supersede                  # or by name, across files
cd web && pnpm build                        # the type-check: tsc -b && vite build
```

Deploying is not a target either: it is a Render Blueprint applied from the dashboard, and the
runbook is [`OPERATIONS.md`](OPERATIONS.md) § *The order*.

**There is no Python type-checker in this repo.** `pyproject.toml` pins pytest, pytest-asyncio and
ruff, and nothing else. `tsc` covers the front end; the back end is covered by tests and by `ruff`,
and that is a deliberate ceiling rather than an oversight.

Two more live in [`../video/`](../video/), for the demo recording: `bash video/reset.sh --check`
reports the demo state without touching it and `bash video/reset.sh` puts it back, against either
store; `video/endcard.sh` renders the video's last frame. [`video-script.md`](video-script.md) is
what they serve.

## The gates

Before calling anything done, all four of these:

```bash
uv run pytest -q          # 321 tests, the 3 that need a database skipped
make db && DATABASE_URL=postgresql://constancia:constancia@localhost:5432/constancia \
  uv run pytest -q        # 321 passed, nothing skipped — run this before touching app/memory.py
uv run ruff check .
cd web && pnpm build      # tsc -b && vite build
grep -rn 'color-neutral-[0-9]\|color-accent-[0-9]' web/src \
  --include='*.tsx' --include='*.ts' --include='*.css' | grep -v tokens.css   # must be empty
```

The last one is the design-system gate: no ramp step may survive outside `tokens.css`. It includes
`.tsx` because some colours live there as data rather than as styles. The reasoning is in
[`FRONTEND.md`](FRONTEND.md). `tests/test_docs.py` walks the same tree in Python and asserts the same
thing, so `make test` already covers it — the shell line stays for the times you want the file and
line printed, and because an unquoted glob in it is how the gate was silently dead before.

There is **no test runner in the front end**. `tsc` is the check: the copy types are built so that a
missing translation fails the build, and presentational components do not earn a test framework.

## Tests

Seventeen test files, 321 collected with no environment variable set. Every one of them passes
except the three Postgres integration tests, which skip themselves.

| File | Covers |
|---|---|
| `tests/conftest.py` | Not a test: one autouse fixture blanks `GEMINI_API_KEY` and `AI_GATEWAY_API_KEY` so the suite cannot reach the network through a filled `.env`, and blanks `DATABASE_URL` for every test that is **not** marked `integration`. `build_llm` (`app/replay.py`) picks the real model the moment a key is readable, so without this `make test` means something different for each person who runs it. The `integration` exemption is not a detail: blanking `DATABASE_URL` for those three sent psycopg to the local socket, so they could only fail, and only for somebody with docker running. |
| `tests/test_orchestrator.py` | The protocol: question order, the red-flag cut, the silence re-prompt, a non-critical phase failing soft, a hangup that still reaches `summarize`, all three packs end to end |
| `tests/test_queries.py` | Multi-step supersession chains, the weekly series per measure, `keyterms_at` as a point-in-time view |
| `tests/test_twilio_routes.py` | The webhooks: TwiML, bad signature, unknown call, a recording URL that is not Twilio's, and the phone fallback down to `DEMO_PHONE` |
| `tests/test_extract.py` | Grounding in all four shapes, retry on invalid JSON, giving up after three, an orphan `supersedes`, a reading off the pack's scale, a quoted request that is not a promise, and an open question with no patient turn behind it, and a promise outside the pack's vocabulary that is dropped alone but kept once the second opinion is asked |
| `tests/test_memory.py` | Seed loading, idempotent `supersede`, key-term filtering by pack, L2 normalisation, and the question queue's whole transition table including the second answer that must move nothing |
| `tests/test_channel.py` | µ-law streaming, waiting on the mark, barge-in that cancels and clears, 100 ms framing, hangup, start timeout, and the confidence floor: a number under it rides along with the turn, one over it does not, and a frame with no `confidence` field doubts nothing |
| `tests/test_sse.py` | Late subscriber gets the buffer, `Last-Event-ID`, keep-alive, unsubscribe, close on `call_ended` |
| `tests/test_analysis.py` | The AssemblyAI request body, `summarize` over a fixture, that `run` never propagates a failure, and the fuzzy alignment of a quote onto the recording's word timings — including one that must not align |
| `tests/test_replay.py` | Scripted week1→week2 with supersession, automatic script choice, the `week2-off` script never quoting last week, the `alarm` script cutting the protocol short, monotonic `export`, fixture playback |
| `tests/test_guard.py` | Rehab's fourteen phrases that must escalate and eighteen that must not, accents and capitals, then the postpartum and chronic rules with their own tables — including the baby's fever, which must not escalate |
| `tests/test_commitments.py` | The four rules that make a quoted sentence a promise: six that score, eight that must not — a request, somebody else's instruction, a habit, an unrelated plan — and what a deadline and a hedge do to the score. Then the vocabulary per vertical: three promises each scored by their own pack and invisible to rehab's. Then the second opinion: three promises no pack enumerates at all, that a rescued promise scores below one the vocabulary matched, and that a sentence with no first-person pledge is dropped **before** anything leaves the process |
| `tests/test_jev.py` | The one network boundary, faked: the keyless gate never opens a connection, a probability over the floor comes back and one under it does not, the floor is the configured one, only the quote and the question cross, and a 403, a timeout, a body that is not JSON, a renamed field and a probability outside 0–1 all answer `None` |
| `tests/test_critic.py` | The four checks between the model and the phone, one positive and one negative each, plus a number grounded by the history rather than the memory block |
| `tests/test_llm.py` | The history the model is handed in all three shapes, and the shared backoff: a rate limit that clears on the third try, and an error that is not retriable |
| `tests/test_docs.py` | The documentation gates, seven of them: every published test count matches the suite, every line anchor in `API.md` still points at what it names, no ramp step survives outside `tokens.css`, every line count in the module tables matches the file, the target table lists every target in the `Makefile`, the published `ponytail:` counts match a real count, and every `docs/*.md` is indexed with no broken relative link |
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
4. The three tests that do need a database mark themselves `integration`, skip without `DATABASE_URL`, and are the one case the autouse fixture leaves that variable alone. They still need no key: `MemoryStore.client` is a `cached_property`, so a store that only runs SQL never builds the Gemini client.
5. Anything that genuinely needs a key lives in `scripts/smoke_*.py` and is run by hand.

`tests/conftest.py` holds one autouse fixture and nothing else. The rest of pytest is configured
in `pyproject.toml`, with `asyncio_mode = "auto"`.

## Conventions

The hard rules are in [`../AGENTS.md`](../AGENTS.md). The ones that bite most often:

- **Everything in the repo is in English** — code, identifiers, docs, commits, PRs. Two exceptions,
  both content rather than code: what the patient hears (`app/packs.py`) and the Spanish half of the
  bilingual interface (the two `copy.ts` and `panel/content.ts`), where English is the annotated base
  and Spanish the translation.
- **No comments**, except `ponytail:` markers naming a deliberate ceiling and its upgrade path.
  There are **66** in the code and they are the honest list of what was knowingly left simple:

  ```bash
  grep -ro 'ponytail:' app/*.py web/src scripts tests schema.sql \
    --exclude-dir=__pycache__ | wc -l
  ```

  `-o` rather than `-c`, because `-c` prints a count per file and the number published here is the
  total. `grep` rather than `git grep`: `git grep` reads the index, so a marker in a file that is
  written and not yet added is invisible to it — which is the state every file is in while the
  change that added the marker is still being made. `tests/test_docs.py` walks the same paths in
  Python and fails when this figure drifts, which it had, twice. Leave the pathspec off and the
  number grows: the docs quote markers too.
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
| Add a red flag | Add a `RedFlag` with its pattern and its message. Use `NEAR` for two-term co-occurrence, or `SELF` when the symptom belongs to the patient and not to somebody they are talking about. Add both a phrase that must escalate and one that must not to `tests/test_guard.py`, and the rule's key to the `rule` map in both halves of `web/src/panel/copy.ts` — that map is a `Record<string, string>`, so `tsc` will not catch a missing one. |
| Add a vertical | Write a pack and register it. Give it a `measure` and `unit` entry in `web/src/panel/copy.ts` for both languages. |
| Add a phase | Add a row to `PHASES` in `app/orchestrator.py` with the same signature as its neighbours, and decide whether it is critical. |
| Add an endpoint | `app/main.py`, before the `StaticFiles` mount — the mount is last on purpose. Update [`API.md`](API.md). |
| Add an interface string | Add it to the `type` in the relevant `copy.ts` first; `tsc` will then tell you every set that is missing it. |
| Change a colour | Only in `web/src/tokens.css`, and only as a semantic alias. Measure the contrast on both themes. |
