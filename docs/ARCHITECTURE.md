# Architecture

One FastAPI process. It places a phone call, runs a fixed sequence of phases over it, turns the
transcript into facts and serves the two pages that show all of it.

```
Twilio ──WS──┐
             │   ┌──────────────────────────────────────┐
AssemblyAI ──┼──▶│  LiveChannel      orchestrator       │──▶ store ──▶ Postgres
             │   │  (say / listen)   (the phases)       │             or the seed
ElevenLabs ──┘   └──────────────────────────────────────┘
                              │ emit()
                              ▼
                     event trace ──SSE──▶ panel
```

The design rule the whole thing hangs on: **the code decides, the model phrases.** Which question
comes next is a `for` loop over a tuple. Whether a call escalates is a regex and a negation check.
The LLM writes sentences and extracts structure; it never chooses.

## One call, end to end

1. `POST /calls` (`app/main.py`) resolves the patient, picks the vertical pack, registers a `Call`
   and branches on `mode`.
2. In `live` mode, `place_call` (`app/telephony.py`) asks Twilio to dial, pointing its webhook at
   `POST /voice` with recording, recording-status and call-status callbacks. It rings for at most
   30 seconds; an unanswered status callback ends the trace without opening a Media Stream.
3. Twilio calls `POST /voice` (`app/main.py`). After the signature check it gets back TwiML that
   connects a bidirectional Media Stream to `wss://.../media/{call_id}`.
4. Twilio opens that socket (`app/main.py`). A `LiveChannel` (`app/channel.py`) connects to
   AssemblyAI and starts both readers, and `run_call` takes over.
5. `run_call` (`app/orchestrator.py`) walks the six phases.
6. After hangup, Twilio posts the recording to `/voice/recording` and the post-call analysis runs as
   a background task.

Everything the call does is emitted onto an append-only trace (`call.emit`), which is what the SSE
stream and the panel's activity rail read. Provenance on screen is the point: a memory claim nobody
can inspect is not worth making.

## The six phases

Declared as data in `PHASES` (`app/orchestrator.py`), walked in order:

| # | Phase | Critical | What it does |
|---|---|---|---|
| 1 | `recall` | no | Loads every current fact for the patient, renders them into the system prompt, and pushes their key terms into the STT's `keyterms_prompt`. |
| 2 | `greet` | **yes** | The LLM writes the greeting — which, with memory on, opens by quoting last week. Then `deliver_answers` speaks any answer the professional left in the queue, word for word and without the model. |
| 3 | `converse` | **yes** | One pass over the question list. Each answer goes through the red-flag guard before it is kept, and a number the recogniser was unsure of earns one read-back turn. |
| 4 | `extract` | no | The transcript becomes structured facts, plus the questions the patient asked and the agent would not answer. |
| 5 | `store` | no | The call row is written **whether or not memory is on** — memory decides what the agent remembers, not whether the call is on the record. With memory on the facts are then embedded and inserted, each one retiring what it contradicts in the same statement; if one fails part way, `facts_lost` names how many did not make it. |
| 6 | `summarize` | no | A summary for the professional, with the new facts named in the prompt, saved onto the call row written in `store`. |

`recall` runs **before** `greet`, not after, so the agent can open on the knee. That is the moment
the project exists to show.

The question list is **not** `pack.questions` any more. `questions_for` (`app/orchestrator.py`)
takes the pack's four and inserts one more before `adherence` when the patient has a standing
promise on file, so the check happens as a question like the others rather than as a branch inside
the loop — which is how it inherits the silence, escalation and answer handling already written
there. `app/replay.py` reads the same function to line the scripted replies up, so the two cannot
drift.

Between the model and the phone sits `app/critic.py`, four deterministic checks on what the model
wrote: no clinical advice, at most two sentences, it has to ask something, and every number in it
has to appear in the memory block or the history. A reply that fails is **not** regenerated — the
question's own `fallback`, written in `app/packs.py`, is spoken instead, which costs no latency at
all on a line where a second model call would cost a second of silence. Only the question loop is
criticised: the greeting, the escalation and the summary have no templated stand-in, and inventing
one for them would mean writing spoken text outside `app/packs.py`.

A **critical** phase that fails breaks the loop, which skips both phases that write the call row, so
`run_call` writes it once more on the way out. A call that died in `greet` is still a call that
happened, and the professional sees it.

The phone hangs up at the end of `converse` (`app/orchestrator.py`): the channel closes and
`ended_at` is set there. Phases 4 to 6 run with the line already dead — a synchronous write during
the call would put dead air on it.

Failures are handled per phase (`app/orchestrator.py`). A `CallEnded` (the patient hung up)
emits `patient_hung_up` and the walk continues, so a call that drops after the second question still
gets extracted, stored and summarised. Any other exception in a critical phase breaks the loop; in a
non-critical one it emits `phase_failed` and moves on. `call_ended` is always emitted once a
call reaches `run_call`. A live call that nobody answers never gets there — the WebSocket only
opens when somebody picks up — so `/voice/status` emits it instead, carrying Twilio's
`CallStatus` as the reason and `unanswered=true`.

`memory=false` short-circuits `recall` entirely and empties `store` of its only interesting half:
the call row is still written, so the call appears in the patient's history, but no fact is extracted
and nothing is superseded (`_memory_off`, `app/orchestrator.py`). Both emit `memory_off` with the
reason, so the panel can say which. Nothing else about the call changes — that is what makes the A/B
honest.

## Memory

A fact is what the patient said, reduced to one sentence, plus the words they used:

```
fact        "right knee pain 7/10 climbing stairs"
term        "right knee"               ← short, feeds the STT's key terms
category    symptom | adherence | mood | clinical_value | red_flag
value       7.0                        ← feeds the chart without parsing text
quote       "hurts seven out of ten"   ← must be a literal span of turn_id
turn_id     4
```

**No quote, no fact.** `ground` (`app/extract.py`) requires the quote to be a literal substring of
the turn with that id, and that turn to be the *patient's* — a quote lifted from the agent's own
question is not evidence. A fact that fails is dropped with `fact_rejected`.

**Contradictions retire, they do not delete.** A new fact that supersedes an old one sets
`superseded_by` and `valid_until` on it (`supersede`, `app/memory.py`). Both stay visible: the
panel draws the chain, current fact on a filled dot and the retired one hanging below it, struck
through, with the window it was true for. "Current" means `valid_until is null and superseded_by is
null`, nothing cleverer.

The extractor is handed **every current fact with its id**, not a top-k vector search. There are
fewer than fifty, and it has to decide `supersedes`, which needs the ids. pgvector stays for the
professional's search in the panel.

## Three modes

The same orchestrator, different collaborators. This is what lets the demo survive an outage, and
what lets the test suite run with no network.

| | `live` | `scripted` | `replay` |
|---|---|---|---|
| Channel | `LiveChannel` | `ScriptedPatient` | none |
| LLM | `GeminiLLM` | `GeminiLLM` if the environment is complete, else `ScriptedLLM` | none |
| Store | the process store | the process store | none |
| Runs the orchestrator | yes | **yes** | no |
| Needs credentials | yes | no | no |

`scripted` is not a mock of the call — it is the real pipeline with a scripted patient on the other
end (`app/channel.py`), so the phase order, the guard, the extraction and the supersession are all
exercised. `build_llm` (`app/replay.py`) is the switch, and its condition is stricter than it looks:
it asks `settings_or_none()` first, so **all eight required variables** have to validate before the
Gemini key is even consulted. Setting `GEMINI_API_KEY` alone leaves `scripted` on `ScriptedLLM`, and
a fully filled `.env` puts the real model behind every keyless button — which is why the test suite
blanks the key rather than trusting that nobody has one. Without it the agent's lines come
from `seed/scripts.json`, keyed by the pack's question ids so that reordering a question raises
`KeyError` instead of silently pairing the wrong sentence with the wrong question. A script that escalates
speaks in a different order — the questions after the red flag are never asked — so it declares its own
`order` list and that one wins (`agent_lines`, `app/replay.py`). `alarm` is the one that does.
There are four: `week1`, `week2`, `week2-off` and `alarm`. `week2-off` exists because the script is
otherwise picked from what the agent recalls, so a memory-off call would travel back to week one
instead of showing the same week without the memory block.


`replay` does not run the orchestrator at all: it re-emits a recorded event trace at its original
pace, capped at 3 seconds between events. The fixtures in `seed/replay/` are produced from `scripted`
mode by `make fixtures`.

## Storage

Two stores behind one duck-typed interface, chosen once in the lifespan (`app/main.py`):

```python
if settings and settings.database_url:
    await asyncio.to_thread(db.init_schema)
    STORE = MemoryStore()
else:
    STORE = load_seed()
```

Postgres with pgvector when `DATABASE_URL` is set and the settings validate; otherwise the JSON seed,
in process. Both return the same columns (`FACT_COLUMNS`, `app/memory.py`), which is why
[`app/queries.py`](../app/queries.py) can be one pure reducer instead of SQL written twice.

> The naming trap: **`MemoryStore` is the Postgres one.** The "memory" in its name is longitudinal
> memory, not RAM. The in-process one is `FakeStore`.

The schema is [`../schema.sql`](../schema.sql), and the Postgres branch above applies it before the
service starts serving — idempotent, so every boot after the first changes nothing, and a deployed
instance never meets an empty database. `make schema` does the same thing by hand.

## System boundaries

These are limits of the current design, not bugs:

- **One worker.** Live calls live in an in-process dict (`CALLS`, `app/calls.py`). Two instances
  would not see each other's calls, and a restart loses the live trace of past calls — the history
  comes back from the database.
- **The panel only follows a call it started itself.** It subscribes with the `call_id` that
  `POST /calls` returned to it; there is no route that lists calls in flight, so a call placed from a
  terminal runs to completion without ever appearing on the page.
- **Extraction runs after hangup**, never during the call. Facts land seconds after the patient stops
  talking.
- **The recording arrives after the facts do.** `analysis.run` is a background task fired by the
  Twilio recording webhook, so by the time the word timings exist the facts are already written.
  Anchoring a quote to its audio is therefore an `UPDATE` on rows that are already there
  (`set_fact_span`), never part of the insert. `scripted` and `replay` have no recording at all, so
  no quote in the offline demo has a play button.
- **A number the recogniser doubted is read back, not re-heard.** The confidence floor only looks at
  words AssemblyAI marks as numbers; a `Turn` frame that carries no `confidence` field leaves the
  read-back switched off rather than firing on everything, which is the degraded mode until a real
  call confirms the field is sent.
- **~1 to 1.5 s of silence per turn**: the LLM writes the whole sentence before the TTS starts.
  Sentence-level streaming is the marked upgrade path.
- **No authentication anywhere.** Anything that can reach the URL can read every patient's history
  and place a call.
- **The trace buffer holds 500 events.** `call.trace` is a bounded `deque` (`TRACE_BUFFER`,
  `app/calls.py`), so a long enough call drops its oldest events from `GET /calls/{id}/trace`, from
  the SSE snapshot a late subscriber receives, and from the exported fixture. It drops them quietly.
- **English only.** The packs are content, so another language is a translation rather
  than a rewrite.

## Where to go next

| You want | Read |
|---|---|
| What each module does | [`BACKEND.md`](BACKEND.md) |
| The routes and their shapes | [`API.md`](API.md) |
| The two pages | [`FRONTEND.md`](FRONTEND.md) |
| Why it was built this way | [`PLAN.md`](PLAN.md), the deviation register at the top |
