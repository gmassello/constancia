# Backend reference

Python 3.12, FastAPI, `uv`. Twenty-two modules, 3,028 lines, no framework beyond FastAPI and no
ORM. [`ARCHITECTURE.md`](ARCHITECTURE.md) has the flow these modules implement; this file is what
each one is for.

## The modules

| Module | Lines | What it is |
|---|---:|---|
| [`app/main.py`](../app/main.py) | 402 | The entry point. Builds the app, picks the store in the lifespan, declares the twenty-four routes and mounts `web/dist` if it exists. `/health` reports both `live` (the credentials validate) and `dialable` (this instance has a demo number of its own), which is what decides whether the panel offers a real call at all. |
| [`app/memory.py`](../app/memory.py) | 465 | The two interchangeable stores, `MemoryStore` (Postgres + pgvector) and `FakeStore` (in process), the seed loader, the `keyterms` computation and the merge that adds the key phrases AssemblyAI heard on the last analysed call. |
| [`app/channel.py`](../app/channel.py) | 310 | The voice channel: `LiveChannel` (Twilio WS ↔ STT ↔ TTS, with barge-in and marks) and `ScriptedPatient`. |
| [`app/packs.py`](../app/packs.py) | 312 | The three verticals as content: system prompt, questions, red-flag patterns, the action vocabulary a promise has to name, measures, and the rendering of the memory block. |
| [`app/orchestrator.py`](../app/orchestrator.py) | 282 | The phase machine. Decides what is said, what is stored and when a call escalates. |
| [`app/llm.py`](../app/llm.py) | 142 | `retrying`, the shared backoff every Gemini call site goes through; `GeminiLLM`; and `ScriptedLLM`, its deterministic double. |
| [`app/replay.py`](../app/replay.py) | 113 | The two modes that need no phone: `run_scripted`, `run_recorded`, and `export`. |
| [`app/extract.py`](../app/extract.py) | 174 | Structured extraction and the grounding check. |
| [`app/analysis.py`](../app/analysis.py) | 162 | Post-call entity detection, sentiment and key phrases on the recording. |
| [`app/commitments.py`](../app/commitments.py) | 80 | The four rules that decide whether a quoted sentence is a promise, and what it scores. Three are generic English and live here; the fourth, the action, is `pack.actions`, because what a patient promises to do is clinical content. Read out of pact and rewritten for patients. When the action vocabulary says no, `recall` asks [`app/jev.py`](../app/jev.py) — but only for a sentence that already pledged something in the first person — and still scores the answer itself. |
| [`app/jev.py`](../app/jev.py) | 78 | The one call to Jev, a typed-decision model reached through Vercel AI Gateway: one boolean question about one sentence, asking the gateway not to retain it and pinning the provider that may serve it. Every failure is a `None`, so the deterministic rules decide alone. |
| [`app/critic.py`](../app/critic.py) | 40 | Four deterministic checks between the model's reply and the phone: clinical advice, length, whether it asks anything, and whether every number in it is on file. |
| [`app/numbers.py`](../app/numbers.py) | 42 | Digits and the words for them, in both languages. One table, because the critic and the STT read-back have to agree on what a number is. |
| [`app/queries.py`](../app/queries.py) | 96 | Pure reducers over fact rows: the chain, the weekly series, the key terms of a past call. |
| [`app/calls.py`](../app/calls.py) | 78 | The `Call` dataclass, the `emit`/`subscribe` event bus, and the global `CALLS` registry. |
| [`app/stt.py`](../app/stt.py) | 69 | AssemblyAI Universal-Streaming v3 over WebSocket, with hot key-term updates. |
| [`app/db.py`](../app/db.py) | 60 | The psycopg async pool, the query helpers and `init_schema()`. |
| [`app/config.py`](../app/config.py) | 58 | `Settings`, `get_settings()`, `settings_or_none()`. |
| [`app/telephony.py`](../app/telephony.py) | 37 | The TwiML and the outbound Twilio call. |
| [`app/guard.py`](../app/guard.py) | 51 | The deterministic red-flag guard. |
| [`app/tts.py`](../app/tts.py) | 30 | ElevenLabs streaming in `ulaw_8000`. |
| [`app/security.py`](../app/security.py) | 24 | The Twilio signature dependency. |

## The four pieces worth reading first

### The orchestrator

`PHASES` (`app/orchestrator.py`) is a tuple of `(name, function, critical)`. Every phase has the
same signature — `(call, channel, llm, store, silence_s)` — so adding one is adding a row.

A critical phase that raises breaks out of the loop, which skips `store` and `summarize` — the two
phases that write the call row. So `run_call` writes it once more after the loop, before
`call_ended`. `save_call` is an upsert on the id, so the third write costs nothing and a call that
died in `greet` still reaches the professional's list instead of vanishing.

`greet` opens generically with nothing on file, and with facts on file it is additionally told to
quote the most recent one back — `GREET_RECALL` in `app/packs.py`, appended only when `call.facts`
is non-empty. That asymmetry is the demo's whole argument, so it is structural rather than left to
the model noticing the memory block: with memory off `recall` returns early, `facts` stays empty,
and the same code path produces the generic opening. The instruction also forbids quoting a number
that is not on file, because a model told it has memory will otherwise invent one.

`converse` is the protocol: one pass over `pack.questions`, in declaration order, no planner.
`phrase()` hands the LLM the system prompt plus a fragment naming the goal; the model writes
the sentence, it does not pick the question. Silence gets exactly one re-prompt (`ask`,
`orchestrator.py:17`), then the call says goodbye.

Two things about `GeminiLLM` are counter-intuitive enough to be worth stating, because both were
live-call failures before they were documented. First, `MAX_OUTPUT_TOKENS` is **not** a length
limiter: Gemini 3 always thinks and the thinking comes out of that same budget, so a tight value
buys an empty reply rather than a short one, and `ThinkingConfig(thinking_budget=0)` does not turn
it off. Two sentences per turn is enforced by `SYSTEM_RULES` in `app/packs.py`. Second, the API
rejects a request whose last turn is the model's. `summarize` always arrives there because `converse`
ends on the goodbye, and `converse` itself arrives there whenever the patient answered nothing, so
`reply()` appends `SILENT_TURN`. That placeholder has to stay **empty of meaning**: it is read as a
patient turn, and anything that reads as a fact about the call gets acted on. `"(end of the call)"`
made the agent say goodbye in place of its first question, on a real call. `make smoke-call` exercises both and prints the token headroom it measured.

Barge-in is not just "did the caller say something while the agent talked". AssemblyAI keeps
emitting `Turn` messages for audio the caller spoke *before* the agent started, so the cutoff is the
`start` of the first word, in milliseconds of caller audio, against how much `LiveChannel` had fed
when it began speaking (`app/channel.py`). Without that comparison the tail of one answer cuts off
the next question and every later answer lands one question late — silently, since the call still
completes.

An interrupted goodbye waits for the patient's formatted final turn before the channel closes. A
turn that finalized while the agent was speaking is kept in the transcript with `heard=false`: its
words still reach the guard and extractor, but it is not attributed as an answer to that question.

A hang-up does not cut the patient off mid-sentence. On Twilio's `stop`, `LiveChannel` sends
AssemblyAI `Terminate` and waits up to `FLUSH_S` (2 s) for the STT reader to finish, so a turn
still finalizing lands in the queue ahead of the hang-up marker. Twilio has closed its side by
then, so from the `stop` on nothing more is sent to it: speech in flight goes nowhere instead of
raising. A `say()` called once the socket has stopped waits for that same flush and then raises
`CallEnded` instead of speaking — it never returns, so nothing downstream can call `listen()` and
serve the turn sitting in the queue as the answer to a question the patient never heard. When
`converse` ends, for any reason — including a critical phase failing on the way — `run_call` runs
the guard over every turn still pending before it closes the channel: a patient who says something
alarming and hangs up still escalates the call, without the spoken escalation line nobody is left
to hear. A hang-up seen in `greet` also skips `converse`: no question is generated for a
line that is already dead, and the post-call phases still run.

### The guard

The rule that governs it is in [`../AGENTS.md`](../AGENTS.md): **the guard is
deterministic code; the LLM phrases the escalation, it never decides on one.**

It runs on **every** patient turn, through `escalated()` — the greeting's included. That is not
symmetry for its own sake: the greeting asks the most open question in the call ("how has your
recovery been going?"), which makes it the likeliest place for an unprompted red flag, and it used
to be the one turn nobody checked. An escalation there ends the call before any question is asked,
because `converse` returns early when `call.escalated` is already set.

`check` (`app/guard.py`) normalises the turn (lowercase, NFD, diacritics dropped — so accents and
capitals do not matter), walks `pack.red_flags` in declaration order and returns the first unnegated
match. `NEGATION` (`app/guard.py`) is applied to the text *before* the match: it looks back at most
twenty characters for a negator, and the window stops at `.`, `,`, `;` or at a conjunction that
opens a new clause, so "I have no energy but I fell yesterday" still escalates. The regex is not
transcribed here on purpose — no gate reads this prose, and the Spanish tokens a previous version
quoted outlived the code by eight commits. A `ponytail:` marker beside it names the ceiling: a
twenty-character window, not a scope parser.

The patterns themselves use `NEAR` (`app/packs.py`) to require two terms to co-occur without
crossing a negation or a full stop. Rehab has four rules, postpartum three and chronic two. The
postpartum fever rule uses `SELF` rather than `NEAR`: the span it allows also excludes third-person
subjects, so "the baby had a fever" does not escalate and "I had a fever" does.

A hit sets `call.escalated`, emits `guard_hit` and **returns immediately** — the remaining questions
are not asked.

### Grounding

`ground` (`app/extract.py`) is six lines and it is the reason the memory claim is checkable:

```python
turn = next((t for t in transcript if t["turn_id"] == fact.turn_id), None)
if not turn or turn["speaker"] != "patient":
    return False
quote = normalize(fact.quote).strip()
return bool(quote) and quote in normalize(turn["text"])
```

Three conditions, all required: the turn exists, it is the patient's, and the quote is a non-blank
literal substring of it. Anything else is dropped with `fact_rejected`. A `supersedes` pointing at an id the
call was not shown is silently nulled (`app/extract.py`) rather than trusted.

`run` makes at most three attempts — the first plus two retries, `MAX_ATTEMPTS` in
`app/extract.py` — feeding Pydantic's own validation error back into the prompt on each failure. `Fact.category` is a `Literal` over `CATEGORIES`, which is what makes that retry
reachable for the error the model is likeliest to make: Pydantic turns the literal into an `enum` in
the schema Gemini receives, so an invented category is refused at the provider, and the retry is the
net underneath. Unconstrained, such a fact used to persist fine and then vanish from the keyterms,
from the weekly chart and — for a red flag written any other way — from the alarm pill, while
`render_facts()` handed it back to the model next week as a valid example.

### The two stores

Same duck-typed interface: `patient`, `patients`, `call`, `calls`, `chain`, `current_facts`, `embed`,
`search`, `save_call`, `insert_fact`, `supersede`, `save_analysis`, `set_fact_span`,
`insert_question`, `questions`, `set_question`. Sixteen methods, and a new one has to land on both
or the panel works against the seed and breaks against Postgres.

| | `MemoryStore` (`app/memory.py`) | `FakeStore` (`app/memory.py`) |
|---|---|---|
| Backing | Postgres + pgvector | lists of dicts from `seed/patients.json` |
| `embed` | Gemini embeddings | `normalize([len(text), 1.0])` |
| `search` | cosine `<=>` with a recency re-rank | substring match |
| `/reset` | refused, `409` | reloads the seed |

> **`MemoryStore` is the Postgres one.** The name means longitudinal memory, not RAM. `store_kind()`
> (`app/main.py`) reports it as `postgres` and `FakeStore` as `seed`.

`supersede` carries `and superseded_by is null` in its `WHERE`, which is what makes retiring the same
fact twice a no-op rather than a second retirement. It is not what the orchestrator calls, though:
`insert_fact` takes the id being replaced and does both in **one statement**, with the insert in a
`WITH` and the retirement as the outer `UPDATE`. `db.execute` opens a connection per statement and
the pool commits on the way out, so two statements are two transactions, and a failure between them
would leave the old fact and the new one both current — the state `app/AGENTS.md` forbids, and the
one that hands the model two contradictory readings of the same measure next week. `where id = null`
matches nothing, so a fact that supersedes nothing needs no branch.

`embed` goes through the same backoff as the completions (`retrying`, `app/llm.py`): same provider,
same key, same quota, so a 429 that the LLM would have absorbed used to drop every fact after the
one it hit. It takes the call's `emit`, so an embedding retry shows up in the rail as `llm_retry`
exactly like a completion retry does. `search` gets that for free, since it embeds the query.

Each fact is still its own transaction, so a failure part way through the loop keeps the ones
already written and loses the rest. `store_facts` emits `facts_lost` naming how many went and which
one failed, then re-raises: the loss is a fact of the architecture, being silent about it was not.

`load_seed` turns the seed's `age_days` into timestamps relative to today and derives
deterministic ids with `uuid5`, so the demo reads as "last week" whenever it is run and the fixtures
keep matching.

## Configuration

`Settings` (`app/config.py`) is `pydantic-settings` reading `.env`. Eight variables are required;
the rest have defaults. `TWILIO_NUMBER` is validated against E.164. The full table is in
[`OPERATIONS.md`](OPERATIONS.md).

Two accessors, and the difference matters:

- `get_settings()` is `@lru_cache`d and **raises** when a required variable is missing.
- `settings_or_none()` swallows the `ValidationError` and returns `None`.

The second one is the degraded mode: with no credentials the service still boots, serves the pages,
runs `scripted` and `replay` calls, and answers every read endpoint that the seed store can serve.
`mode=live` is refused, and so is `GET /search`, which needs pgvector and answers `503` without it.

`DEMO_PHONE` is the one optional setting that `POST /calls` reads on the request path: the number a
seeded patient is dialled at, last in the chain after `request.phone` and the patient row
(`app/main.py`). The seed ships with an empty `phone_e164`, so without it a live call on a
seeded patient is a `400` rather than a call to a plausible-looking number that cannot exist.

It is also why `DATABASE_URL` alone does not switch the store: the lifespan reads it off
`settings_or_none()`, which is `None` until all eight required variables validate. When it is not
`None` and carries a database, the lifespan applies `schema.sql` in a thread before building
`MemoryStore` — `init_schema()` (`app/db.py`) is synchronous psycopg, and the DDL is idempotent.

### The import-time rule

From [`../AGENTS.md`](../AGENTS.md): **`get_settings()` is called from the lifespan or from a request,
never at import time. Importing `app.main` with no environment must not raise.**

Two consequences visible throughout the code, and both are deliberate:

1. SDK clients are imported **inside** the function or property that uses them — `from google
   import genai` sits in `app/llm.py` and `app/memory.py`, not at the top of the module.
   `MemoryStore.client` is a `cached_property` for the same reason one step further in: everything
   else on that store is SQL, so a constructor that opened a network client made the store
   unusable against a real database without a real key.
2. Every module that needs a credential asks for it at call time: `app/stt.py`, `app/tts.py`,
   `app/telephony.py`, `app/security.py`, `app/analysis.py`, `app/db.py`.

`tests/test_import_safety.py` is what keeps this true.

## Conventions

- **No comments**, except `ponytail:` markers naming a deliberate ceiling and its upgrade path.
  There are **44** on this side — 44 in `app/` plus one in `schema.sql` — and they are the honest
  list of what was knowingly left simple. The densest are the ten in `app/orchestrator.py`, which
  are where the phase machine explains itself, then eight in `app/memory.py`, six in `app/main.py`,
  five in `app/analysis.py` and three each in `app/channel.py` and `app/llm.py`. The gate counts
  them by walking the tree in `tests/test_docs.py`, not with `git grep`, because a marker in a file
  that is written and not yet added is still a marker:

  ```bash
  grep -ro 'ponytail:' app/*.py schema.sql | wc -l
  ```
- **Exact versions** (`==`) in `pyproject.toml`; `uv.lock` is committed.
- **The transcript is data, never instructions.** Nothing the patient says is executed or treated as
  a directive to the model.
- **Everything the agent says lives in `app/packs.py`** — prompt fragments, questions, escalation and goodbye
  lines. Everything else in the repo is English.

See [`WORKING.md`](WORKING.md) for the commands and the verification gates.
