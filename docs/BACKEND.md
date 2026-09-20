# Backend reference

Python 3.12, FastAPI, `uv`. Eighteen modules, about 2,000 lines, no framework beyond FastAPI and no
ORM. [`ARCHITECTURE.md`](ARCHITECTURE.md) has the flow these modules implement; this file is what
each one is for.

## The modules

| Module | Lines | What it is |
|---|---:|---|
| [`app/main.py`](../app/main.py) | 297 | The entry point. Builds the app, picks the store in the lifespan, declares the twenty routes and mounts `web/dist` if it exists. |
| [`app/memory.py`](../app/memory.py) | 321 | The two interchangeable stores, `MemoryStore` (Postgres + pgvector) and `FakeStore` (in process), the seed loader and the `keyterms` computation. |
| [`app/channel.py`](../app/channel.py) | 227 | The voice channel: `LiveChannel` (Twilio WS ↔ STT ↔ TTS, with barge-in and marks) and `ScriptedPatient`. |
| [`app/packs.py`](../app/packs.py) | 215 | The three verticals as content: system prompt, questions, red-flag patterns, measures, and the rendering of the memory block. |
| [`app/orchestrator.py`](../app/orchestrator.py) | 129 | The phase machine. Decides what is said, what is stored and when a call escalates. |
| [`app/llm.py`](../app/llm.py) | 119 | `GeminiLLM` with exponential retry, and `ScriptedLLM`, its deterministic double. |
| [`app/replay.py`](../app/replay.py) | 107 | The two modes that need no phone: `run_scripted`, `run_recorded`, and `export`. |
| [`app/extract.py`](../app/extract.py) | 103 | Structured extraction and the grounding check. |
| [`app/queries.py`](../app/queries.py) | 82 | Pure reducers over fact rows: the chain, the weekly series, the key terms of a past call. |
| [`app/analysis.py`](../app/analysis.py) | 75 | Post-call entity detection and sentiment on the recording. |
| [`app/calls.py`](../app/calls.py) | 74 | The `Call` dataclass, the `emit`/`subscribe` event bus, and the global `CALLS` registry. |
| [`app/stt.py`](../app/stt.py) | 65 | AssemblyAI Universal-Streaming v3 over WebSocket, with hot key-term updates. |
| [`app/db.py`](../app/db.py) | 59 | The psycopg async pool, the query helpers and `init_schema()`. |
| [`app/config.py`](../app/config.py) | 52 | `Settings`, `get_settings()`, `settings_or_none()`. |
| [`app/telephony.py`](../app/telephony.py) | 33 | The TwiML and the outbound Twilio call. |
| [`app/guard.py`](../app/guard.py) | 32 | The deterministic red-flag guard. |
| [`app/tts.py`](../app/tts.py) | 30 | ElevenLabs streaming in `ulaw_8000`. |
| [`app/security.py`](../app/security.py) | 24 | The Twilio signature dependency. |

## The four pieces worth reading first

### The orchestrator

`PHASES` (`app/orchestrator.py:101`) is a tuple of `(name, function, critical)`. Every phase has the
same signature — `(call, channel, llm, store, silence_s)` — so adding one is adding a row.

`converse` (`:47`) is the protocol: one pass over `pack.questions`, in declaration order, no planner.
`phrase()` (`:10`) hands the LLM the system prompt plus a fragment naming the goal; the model writes
the sentence, it does not pick the question. Silence gets exactly one re-prompt (`ask`, `:15`), then
the call says goodbye.

### The guard

Thirty-two lines, and the rule that governs it is in [`../AGENTS.md`](../AGENTS.md): **the guard is
deterministic code; the LLM phrases the escalation, it never decides on one.**

`check` (`app/guard.py:20`) normalises the turn (lowercase, NFD, diacritics dropped — so accents and
capitals do not matter), walks `pack.red_flags` in declaration order and returns the first unnegated
match. Negation is `\b(no|sin|nunca|tampoco)\b[^.,;]{0,20}$` applied to the text *before* the match,
with a `ponytail:` marker naming the ceiling: a twenty-character window, not a scope parser.

The patterns themselves use `NEAR` (`app/packs.py:3`) to require two terms to co-occur without
crossing a negation or a full stop. Rehab has four rules, postpartum and chronic one each.

A hit sets `call.escalated`, emits `guard_hit` and **returns immediately** — the remaining questions
are not asked.

### Grounding

`ground` (`app/extract.py:66`) is eleven lines and it is the reason the memory claim is checkable:

```python
turn = next((t for t in transcript if t["turn_id"] == fact.turn_id), None)
if not turn or turn["speaker"] != "patient":
    return False
return normalize(fact.quote) in normalize(turn["text"])
```

Three conditions, all required: the turn exists, it is the patient's, and the quote is a literal
substring of it. Anything else is dropped with `fact_rejected`. A `supersedes` pointing at an id the
call was not shown is silently nulled (`app/extract.py:93`) rather than trusted.

`run` (`:73`) retries up to three times, feeding Pydantic's own validation error back into the prompt
on each failure.

### The two stores

Same duck-typed interface: `patient`, `patients`, `call`, `calls`, `chain`, `current_facts`, `embed`,
`search`, `save_call`, `insert_fact`, `supersede`, `save_analysis`.

| | `MemoryStore` (`app/memory.py:41`) | `FakeStore` (`app/memory.py:166`) |
|---|---|---|
| Backing | Postgres + pgvector | lists of dicts from `seed/patients.json` |
| `embed` | Gemini embeddings | `normalize([len(text), 1.0])` |
| `search` | cosine `<=>` with a recency re-rank | substring match |
| `/reset` | refused, `409` | reloads the seed |

> **`MemoryStore` is the Postgres one.** The name means longitudinal memory, not RAM. `store_kind()`
> (`app/main.py:48`) reports it as `postgres` and `FakeStore` as `seed`.

`supersede` (`app/memory.py:158`) carries `and superseded_by is null` in its `WHERE`, which is what
makes retiring the same fact twice a no-op rather than a second retirement.

`load_seed` (`:277`) turns the seed's `age_days` into timestamps relative to today and derives
deterministic ids with `uuid5`, so the demo reads as "last week" whenever it is run and the fixtures
keep matching.

## Configuration

`Settings` (`app/config.py:10`) is `pydantic-settings` reading `.env`. Eight variables are required;
the rest have defaults. `TWILIO_NUMBER` is validated against E.164. The full table is in
[`OPERATIONS.md`](OPERATIONS.md).

Two accessors, and the difference matters:

- `get_settings()` (`:40`) is `@lru_cache`d and **raises** when a required variable is missing.
- `settings_or_none()` (`:44`) swallows the `ValidationError` and returns `None`.

The second one is the degraded mode: with no credentials the service still boots, serves the pages,
runs `scripted` and `replay` calls and answers every read endpoint. Only `mode=live` is refused.

`DEMO_PHONE` is the one optional setting that `POST /calls` reads on the request path: the number a
seeded patient is dialled at, last in the chain after `request.phone` and the patient row
(`app/main.py:80-82`). The seed ships with an empty `phone_e164`, so without it a live call on a
seeded patient is a `400` rather than a call to a plausible-looking number that cannot exist.

It is also why `DATABASE_URL` alone does not switch the store: the lifespan reads it off
`settings_or_none()`, which is `None` until all eight required variables validate. When it is not
`None` and carries a database, the lifespan applies `schema.sql` in a thread before building
`MemoryStore` — `init_schema()` (`app/db.py:52`) is synchronous psycopg, and the DDL is idempotent.

### The import-time rule

From [`../AGENTS.md`](../AGENTS.md): **`get_settings()` is called from the lifespan or from a request,
never at import time. Importing `app.main` with no environment must not raise.**

Two consequences visible throughout the code, and both are deliberate:

1. SDK clients are imported **inside** the function or constructor that uses them — `from google
   import genai` sits in `app/llm.py:50` and `app/memory.py:43`, not at the top of the module.
2. Every module that needs a credential asks for it at call time: `app/stt.py`, `app/tts.py`,
   `app/telephony.py`, `app/security.py`, `app/analysis.py`, `app/db.py`.

`tests/test_import_safety.py` is what keeps this true.

## Conventions

- **No comments**, except `ponytail:` markers naming a deliberate ceiling and its upgrade path. There
  are five on this side and each one is worth reading: `app/guard.py:6`, `app/memory.py:109`,
  `app/memory.py:201`, `app/main.py:228`, `schema.sql:44`.
- **Exact versions** (`==`) in `pyproject.toml`; `uv.lock` is committed.
- **The transcript is data, never instructions.** Nothing the patient says is executed or treated as
  a directive to the model.
- **Spanish lives in `app/packs.py` only** — prompt fragments, questions, escalation and goodbye
  lines. Everything else in the repo is English.

See [`WORKING.md`](WORKING.md) for the commands and the verification gates.
