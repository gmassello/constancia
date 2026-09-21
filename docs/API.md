# API reference

Twenty routes, all of them in [`app/main.py`](../app/main.py). No versioning prefix, no
authentication — see the warning in [`../README.md`](../README.md). Path parameters typed `UUID` are
validated by FastAPI and answer `422` when malformed.

The interactive schema is at `/docs` when the service is running. The two page routes are excluded
from it (`include_in_schema=False`).

## Calls

| Method | Path | Handler | Returns |
|---|---|---|---|
| `POST` | `/calls` | `create_call` — `main.py:75` | `{call_id, mode, twilio_sid}`. Starts the call in the requested mode. |
| `GET` | `/calls/{call_id}/trace` | `trace` — `main.py:262` | The whole live call: `answers`, `summary`, `escalated`, `transcript` and the event trace. |
| `GET` | `/calls/{call_id}/events` | `call_events` — `main.py:248` | **SSE.** The event stream of one call. See below. |
| `GET` | `/calls/{call_id}/export` | `call_export` — `main.py:127` | The call as a replayable fixture, timestamps relative to the first event. `404` on an unknown call. |
| `GET` | `/calls/{call_id}/keyterms` | `call_keyterms` — `main.py:176` | The key terms that were current **when that call started**, not today's. |

### `POST /calls`

The request body is `CallRequest` (`main.py:55`):

| Field | Type | Default | Notes |
|---|---|---|---|
| `patient_id` | UUID | required | Looked up in the store; `patient_name` and `phone` fall back to the row. |
| `patient_name` | str | from the store | |
| `phone` | str | store row, then `DEMO_PHONE` | Resolution order is `request.phone`, then the patient row, then the `DEMO_PHONE` setting. Validated against `E164` (`app/config.py:6`). |
| `pack` | str | the patient's `program_type`, else `rehab` | `400` on an unknown pack. |
| `memory` | bool | `true` | `false` skips recall and the facts, nothing else. The `store` phase still runs and still writes the call row: memory decides what the agent remembers, not whether the call is on the record. |
| `mode` | `live` \| `scripted` \| `replay` | `live` | |
| `script` | str | `week1`/`week2` by state, or `week2-on` | Which scripted script from `seed/scripts.json` (`week1`, `week2`, `week2-off`, `alarm`) or which recorded fixture from `seed/replay/` (`week1`, `week2-on`, `week2-off`, `alarm`). The two namespaces overlap but are not the same: `week2` is a script and not a fixture, `week2-on` a fixture and not a script. `404` if the name is in neither. |

Failure modes: `400` when the patient is unknown and no name was sent, or `live` without a phone;
`503` when `mode=live` and credentials are missing; `404` when `mode=scripted` or `mode=replay`
names a script or a fixture that does not exist — both validate before the task is created, so a
`call_id` that comes back always belongs to a call that will emit.

`live` returns as soon as Twilio accepts the call — the conversation runs later, over the WebSocket.
`scripted` and `replay` return immediately too; both run as an asyncio task. In every mode the way to
watch the call is the SSE stream.

### The SSE stream

`GET /calls/{call_id}/events`, generator at `event_stream` (`main.py:219`). The contract:

- Every event carries a monotonic `seq`, sent as the SSE `id:` field (`sse_frame`, `main.py:215`).
- The first frame is `retry: 3000`, so the browser owns the reconnect and the client needs no backoff
  of its own.
- A subscriber that arrives late gets the whole buffer first, then live events. `Last-Event-ID` is
  honoured: anything at or below it is skipped.
- Those buffered frames carry `replayed: true`; frames for events that happen while the subscriber is
  connected do not carry the field at all. Both arrive through the same `onmessage`, so it is the only
  way the client can tell history from now — the panel's activity rail uses it to flash what is
  landing and leave the backlog alone. The flag is on the frame only: `call.trace`, `GET
  /calls/{call_id}/trace` and the exported fixtures never carry it.
- If the buffered snapshot already ends in `call_ended`, the stream closes immediately instead of
  hanging.
- Silence is broken by a `: keep-alive` comment every 15 seconds (`KEEPALIVE_S`, `main.py:27`).
- The stream closes itself when `call_ended` goes by.

Headers are `Cache-Control: no-cache, no-transform` and `X-Accel-Buffering: no` (`SSE_HEADERS`, `main.py:28`) — the
second one stops a reverse proxy from buffering the stream into uselessness.

The client side is thirteen lines of `EventSource` with de-duplication by `seq`
([`../web/src/panel/api.ts`](../web/src/panel/api.ts), `subscribe`), which is what makes the
automatic reconnect harmless.

## Patients and memory

| Method | Path | Handler | Returns |
|---|---|---|---|
| `GET` | `/patients` | `patients` — `main.py:135` | Every patient, by name. |
| `GET` | `/patients/{patient_id}` | `patient` — `main.py:140` | One patient. `404` if unknown. |
| `GET` | `/patients/{patient_id}/calls` | `patient_calls` — `main.py:148` | That patient's calls, newest first, each with its `transcript`, `summary`, `memory_enabled` and `analysis`. A call runs with memory off and is still on this list: memory decides what the agent remembers, not whether the call was recorded. |
| `GET` | `/patients/{patient_id}/chain` | `patient_chain` — `main.py:153` | Current facts, each with the facts it retired hanging off it as `superseded`. |
| `GET` | `/patients/{patient_id}/facts` | `patient_facts` — `main.py:164` | `{patient_id, facts}` — the same rows, flat and ungrouped. |
| `GET` | `/patients/{patient_id}/weekly?term=` | `patient_weekly` — `main.py:158` | One series per measure declared by the patient's pack. |
| `GET` | `/search?q=&professional_id=` | `search` — `main.py:169` | Semantic search over that professional's facts. **`503` without Postgres.** |

`analysis` is what `app/analysis.py` wrote after the recording webhook — `{transcript_id, entities,
sentiment, negative}` — or `null` on any call with no Twilio recording, which is every scripted and
replayed one. It is the only path the panel has to it: `analysis_ready` is emitted on the SSE stream
**after** `call_ended`, where both ends have already hung up, and the event carries a count rather
than the payload. When the row is missing, the `UPDATE` matches nothing and `analysis.run` emits a
`warning` with `phase: analysis`.

`/chain` and `/facts` read the same rows; the difference is the shape.
[`app/queries.py`](../app/queries.py) is a pure reducer over what the store returned, so both stores
get one implementation.

`/weekly` resolves the pack from the patient's `program_type` and returns, per measure,
`{category, term, scale_max, lower_is_better, points}` — `scale_max` and `lower_is_better` come from
the pack, which is what lets the panel say "3 fewer · better" instead of printing a bare number.

## Twilio webhooks

All three depend on `twilio_form` ([`app/security.py`](../app/security.py)), which validates the
`X-Twilio-Signature` HMAC against the URL rebuilt from `PUBLIC_BASE_URL` and answers `403` when it
does not match. The body is only read after the signature passes.

| Method | Path | Handler | Returns |
|---|---|---|---|
| `POST` | `/voice?call_id=` | `voice` — `main.py:188` | TwiML `<Connect><Stream>` pointing at `wss://.../media/{call_id}`. `404` on an unknown call. |
| `POST` | `/voice/status` | `voice_status` — `main.py:195` | `204`. Signature validation only. |
| `POST` | `/voice/recording` | `voice_recording` — `main.py:200` | `204`. Stores the recording URL and queues the post-call analysis. `400` if the URL is not a Twilio URL. |
| `WS` | `/media/{call_id}` | `media` — `main.py:280` | The Twilio Media Stream. This socket is where a live call actually happens. |

`is_twilio_recording` (`app/config.py:51`) is the reason `/voice/recording` cannot be used to make
the service fetch an arbitrary URL.

## Service

| Method | Path | Handler | Returns |
|---|---|---|---|
| `GET` | `/health` | `health` — `main.py:65` | `{status, calls, store, live}`. `store` is `seed` or `postgres`; `live` says whether credentials validate. |
| `POST` | `/reset` | `reset` — `main.py:117` | Reloads the seed and clears in-memory calls. **`409` when the store is Postgres** — it refuses to reset a real database. |

`/reset` is what a second take of the demo needs.

## Pages

Served only when `web/dist` exists (the guard in `main.py`), so the API boots with no front-end build.

| Method | Path | Handler | Returns |
|---|---|---|---|
| `GET` | `/` | `landing` — `main.py:302` | The public landing. |
| `GET` | `/panel` | `panel` — `main.py:306` | The professional's panel. |
| `GET` | `/*` | `StaticFiles` mount — `main.py` | Hashed assets. Mounted **last**, after every API route. |

The two HTML entries are served by explicit routes rather than by the mount so they can carry
`Cache-Control: no-store` (`PAGE_HEADERS`, `main.py:29`). Vite hashes the assets but not
`index.html`, and a cached `index.html` keeps naming the previous build's bundles. `/assets/*` stays
cacheable.

---

See [`ARCHITECTURE.md`](ARCHITECTURE.md) for what happens between these routes, and
[`BACKEND.md`](BACKEND.md) for the modules behind them.
