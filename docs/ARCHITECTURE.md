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

1. `POST /calls` (`app/main.py:75`) resolves the patient, picks the vertical pack, registers a `Call`
   and branches on `mode`.
2. In `live` mode, `place_call` (`app/telephony.py:21`) asks Twilio to dial, pointing its webhook at
   `POST /voice` with `record=True`.
3. Twilio calls `POST /voice` (`app/main.py:183`). After the signature check it gets back TwiML that
   connects a bidirectional Media Stream to `wss://.../media/{call_id}`.
4. Twilio opens that socket (`app/main.py:271`). A `LiveChannel` (`app/channel.py:61`) connects to
   AssemblyAI and starts both readers, and `run_call` takes over.
5. `run_call` (`app/orchestrator.py:111`) walks the six phases.
6. After hangup, Twilio posts the recording to `/voice/recording` and the post-call analysis runs as
   a background task.

Everything the call does is emitted onto an append-only trace (`call.emit`), which is what the SSE
stream and the panel's activity rail read. Provenance on screen is the point: a memory claim nobody
can inspect is not worth making.

## The six phases

Declared as data in `PHASES` (`app/orchestrator.py:101`), walked in order:

| # | Phase | Critical | What it does |
|---|---|---|---|
| 1 | `recall` | no | Loads every current fact for the patient, renders them into the system prompt, and pushes their key terms into the STT's `keyterms_prompt`. |
| 2 | `greet` | **yes** | The LLM writes the greeting — which, with memory on, opens by quoting last week. |
| 3 | `converse` | **yes** | One pass over `pack.questions`. Each answer goes through the red-flag guard before it is kept. |
| 4 | `extract` | no | The transcript becomes structured facts. |
| 5 | `store` | no | The call row is written, the facts are embedded and inserted, and the ones they contradict are retired. |
| 6 | `summarize` | no | A summary for the professional, with the new facts named in the prompt, saved onto the call row written in `store`. |

`recall` runs **before** `greet`, not after, so the agent can open on the knee. That is the moment
the project exists to show.

The phone hangs up at the end of `converse` (`app/orchestrator.py:125-127`): the channel closes and
`ended_at` is set there. Phases 4 to 6 run with the line already dead — a synchronous write during
the call would put dead air on it.

Failures are handled per phase (`app/orchestrator.py:117-124`). A `CallEnded` (the patient hung up)
emits `patient_hung_up` and the walk continues, so a call that drops after the second question still
gets extracted, stored and summarised. Any other exception in a critical phase breaks the loop; in a
non-critical one it emits `phase_failed` and moves on. `call_ended` is always emitted.

`memory=false` short-circuits exactly two phases, `recall` and `store` (`_memory_off`,
`app/orchestrator.py:24`), and emits `memory_off` with the reason so the panel can say which. Nothing
else about the call changes — that is what makes the A/B honest.

## Memory

A fact is what the patient said, reduced to one sentence, plus the words they used:

```
fact        "dolor en la rodilla derecha 7/10 al subir escaleras"
term        "rodilla derecha"          ← short, feeds the STT's key terms
category    symptom | adherence | mood | clinical_value | red_flag
value       7.0                        ← feeds the chart without parsing text
quote       "me duele siete de diez"   ← must be a literal span of turn_id
turn_id     4
```

**No quote, no fact.** `ground` (`app/extract.py:66`) requires the quote to be a literal substring of
the turn with that id, and that turn to be the *patient's* — a quote lifted from the agent's own
question is not evidence. A fact that fails is dropped with `fact_rejected`.

**Contradictions retire, they do not delete.** A new fact that supersedes an old one sets
`superseded_by` and `valid_until` on it (`supersede`, `app/memory.py:158`). Both stay visible: the
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
| LLM | `GeminiLLM` | `GeminiLLM` if a key exists, else `ScriptedLLM` | none |
| Store | the process store | the process store | none |
| Runs the orchestrator | yes | **yes** | no |
| Needs credentials | yes | no | no |

`scripted` is not a mock of the call — it is the real pipeline with a scripted patient on the other
end (`app/channel.py:22`), so the phase order, the guard, the extraction and the supersession are all
exercised. `build_llm` (`app/replay.py:36`) is the switch; with no Gemini key the agent's lines come
from `seed/scripts.json`, keyed by the pack's question ids so that reordering a question raises
`KeyError` instead of silently pairing the wrong sentence with the wrong question. A script that escalates
speaks in a different order — the questions after the red flag are never asked — so it declares its own
`order` list and that one wins (`agent_lines`, `app/replay.py:31`). `alarm` is the one that does.

`replay` does not run the orchestrator at all: it re-emits a recorded event trace at its original
pace, capped at 3 seconds between events. The fixtures in `seed/replay/` are produced from `scripted`
mode by `make fixtures`.

## Storage

Two stores behind one duck-typed interface, chosen once in the lifespan (`app/main.py:39`):

```python
if settings and settings.database_url:
    await asyncio.to_thread(db.init_schema)
    STORE = MemoryStore()
else:
    STORE = load_seed()
```

Postgres with pgvector when `DATABASE_URL` is set and the settings validate; otherwise the JSON seed,
in process. Both return the same columns (`FACT_COLUMNS`, `app/memory.py:16`), which is why
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
- **Extraction runs after hangup**, never during the call. Facts land seconds after the patient stops
  talking.
- **~1 to 1.5 s of silence per turn**: the LLM writes the whole sentence before the TTS starts.
  Sentence-level streaming is the marked upgrade path.
- **No authentication anywhere.** Anything that can reach the URL can read every patient's history
  and place a call.
- **Spanish only** (Rioplatense). The packs are content, so another language is a translation rather
  than a rewrite.

## Where to go next

| You want | Read |
|---|---|
| What each module does | [`BACKEND.md`](BACKEND.md) |
| The routes and their shapes | [`API.md`](API.md) |
| The two pages | [`FRONTEND.md`](FRONTEND.md) |
| Why it was built this way | [`PLAN.md`](PLAN.md), the deviation register at the top |
