import asyncio
import json
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Annotated, Literal
from uuid import UUID

import httpx
from fastapi import BackgroundTasks, Depends, FastAPI, HTTPException, Request, Response, WebSocket
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from starlette.datastructures import FormData

from app import analysis, db, queries, replay
from app.calls import CALLS, Call, register
from app.channel import CallEnded, LiveChannel
from app.config import E164, get_settings, is_twilio_recording, settings_or_none
from app.llm import GeminiLLM
from app.memory import MemoryStore, load_seed
from app.orchestrator import run_call
from app.packs import get_pack
from app.security import twilio_form
from app.telephony import place_call, stream_twiml

STORE = None
KEEPALIVE_S = 15.0
SSE_HEADERS = {"Cache-Control": "no-cache, no-transform", "X-Accel-Buffering": "no"}
PAGE_HEADERS = {"Cache-Control": "no-store"}
DEFAULT_FIXTURE = "week2-on"
AUDIO_TIMEOUT_S = 30.0
WEB_DIST = Path(__file__).resolve().parent.parent / "web" / "dist"


@asynccontextmanager
async def lifespan(app: FastAPI):
    global STORE
    settings = settings_or_none()
    if settings and settings.database_url:
        await asyncio.to_thread(db.init_schema)
        STORE = MemoryStore()
    else:
        STORE = load_seed()
    yield
    STORE = None
    await db.close_pool()


def store_kind() -> str:
    return "postgres" if isinstance(STORE, MemoryStore) else "seed"


app = FastAPI(title="constancia", lifespan=lifespan)


class CallRequest(BaseModel):
    patient_id: UUID
    patient_name: str | None = None
    phone: str | None = Field(default=None, pattern=E164)
    pack: str | None = None
    memory: bool = True
    mode: Literal["live", "scripted", "replay"] = "live"
    script: str | None = None


class AnswerRequest(BaseModel):
    answer: str = Field(min_length=1, max_length=400)


@app.get("/health")
async def health() -> dict:
    return {
        "status": "ok",
        "calls": len(CALLS),
        "store": store_kind(),
        "live": settings_or_none() is not None,
    }


@app.post("/calls")
async def create_call(request: CallRequest) -> dict:
    patient_id = str(request.patient_id)
    row = await STORE.patient(patient_id) if STORE else None
    name = request.patient_name or (row or {}).get("name")
    settings = settings_or_none()
    demo_phone = settings.demo_phone if settings else ""
    phone = request.phone or (row or {}).get("phone_e164") or demo_phone
    if not name or (request.mode == "live" and not phone):
        raise HTTPException(status_code=400, detail="unknown patient: send patient_name and phone")
    try:
        pack = get_pack(request.pack or (row or {}).get("program_type") or "rehab")
    except KeyError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    if request.mode == "live" and not settings:
        raise HTTPException(status_code=503, detail="live mode needs credentials")
    if request.mode == "scripted" and request.script and request.script not in replay.scripts():
        raise HTTPException(status_code=404, detail=f"no script named {request.script}")
    if request.mode == "replay":
        try:
            replay.load_fixture(request.script or DEFAULT_FIXTURE)
        except FileNotFoundError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
    call = register(
        Call(
            patient_id=patient_id,
            patient_name=name,
            pack=pack,
            memory=request.memory,
        )
    )
    if request.mode == "live":
        call.twilio_sid = place_call(call.id, phone)
    elif request.mode == "scripted":
        call.task = _watched(call, replay.run_scripted(call, STORE, request.script))
    else:
        call.task = _watched(call, replay.run_recorded(call, request.script or DEFAULT_FIXTURE))
    return {"call_id": call.id, "mode": request.mode, "twilio_sid": call.twilio_sid}


# ponytail: `run_call` wraps every phase, but the lines around it do not — picking the script,
# reading the current facts, building the LLM. A task that dies there emits nothing at all, and the
# panel cannot tell that from a call still dialling, so the death is reported as the call ending.
def _watched(call: Call, coroutine) -> asyncio.Task:
    def ended(task: asyncio.Task) -> None:
        if task.cancelled() or task.exception() is None:
            return
        if any(event["type"] == "call_ended" for event in call.trace):
            return
        call.emit("phase_failed", phase="call", critical=True, error=repr(task.exception()))
        call.emit("call_ended", escalated=bool(call.escalated), answers=dict(call.answers))

    task = asyncio.create_task(coroutine)
    task.add_done_callback(ended)
    return task


@app.post("/reset")
async def reset() -> dict:
    global STORE
    if store_kind() == "postgres":
        raise HTTPException(status_code=409, detail="refusing to reset a real database")
    STORE = load_seed()
    CALLS.clear()
    return {"status": "ok", "store": store_kind()}


@app.get("/calls/{call_id}/export")
async def call_export(call_id: str) -> dict:
    call = CALLS.get(call_id)
    if not call:
        raise HTTPException(status_code=404, detail="unknown call")
    return replay.export(call)


@app.get("/patients")
async def patients() -> list[dict]:
    return await STORE.patients()


@app.get("/patients/{patient_id}")
async def patient(patient_id: UUID) -> dict:
    row = await STORE.patient(str(patient_id))
    if not row:
        raise HTTPException(status_code=404, detail="unknown patient")
    return row


@app.get("/patients/{patient_id}/calls")
async def patient_calls(patient_id: UUID) -> list[dict]:
    return await STORE.calls(str(patient_id))


@app.get("/patients/{patient_id}/chain")
async def patient_chain(patient_id: UUID) -> list[dict]:
    return queries.chain(await STORE.chain(str(patient_id)))


@app.get("/patients/{patient_id}/weekly")
async def patient_weekly(patient_id: UUID, term: str | None = None) -> list[dict]:
    pack_key = (await STORE.patient(str(patient_id)) or {}).get("program_type", "rehab")
    return queries.weekly(await STORE.chain(str(patient_id)), get_pack(pack_key), term)


@app.get("/patients/{patient_id}/facts")
async def patient_facts(patient_id: UUID) -> dict:
    return {"patient_id": str(patient_id), "facts": await STORE.chain(str(patient_id))}


@app.get("/patients/{patient_id}/questions")
async def patient_questions(patient_id: UUID) -> list[dict]:
    return await STORE.questions(str(patient_id))


@app.post("/questions/{question_id}/answer")
async def answer_question(question_id: str, body: AnswerRequest) -> dict:
    # ponytail: ordered by recency, not by how often it was asked. Vera counts repeats because a
    # gap is shared across its users; here a row belongs to one patient, so the count is always one.
    if not await STORE.set_question(question_id, "open", "answered", body.answer):
        raise HTTPException(status_code=409, detail="that question is not open")
    return {"question_id": question_id, "status": "answered"}


@app.post("/questions/{question_id}/dismiss")
async def dismiss_question(question_id: str) -> dict:
    if not await STORE.set_question(question_id, "open", "dismissed"):
        raise HTTPException(status_code=409, detail="that question is not open")
    return {"question_id": question_id, "status": "dismissed"}


@app.get("/search")
async def search(q: str, professional_id: UUID) -> list[dict]:
    if store_kind() != "postgres":
        raise HTTPException(status_code=503, detail="search needs a database")
    return await STORE.search(str(professional_id), q)


@app.get("/calls/{call_id}/keyterms")
async def call_keyterms(call_id: str) -> list[str]:
    row = await STORE.call(call_id)
    if not row:
        raise HTTPException(status_code=404, detail="unknown call")
    patient_id = str(row["patient_id"])
    pack_key = (await STORE.patient(patient_id) or {}).get("program_type", "rehab")
    return queries.keyterms_at(
        await STORE.chain(patient_id), row["started_at"], get_pack(pack_key)
    )


@app.get("/calls/{call_id}/audio")
async def call_audio(call_id: str) -> Response:
    # ponytail: the whole mp3 in one response, no Range. A five minute call is well under a
    # megabyte, so the browser buffers it and seeks to the media fragment itself. Serve 206s the
    # day a call is long enough for that to feel slow.
    row = await STORE.call(call_id)
    url = (row or {}).get("recording_url")
    if not row or not url:
        raise HTTPException(status_code=404, detail="that call has no recording")
    if not is_twilio_recording(url):
        raise HTTPException(status_code=400, detail="not a twilio recording")
    settings = get_settings()
    async with httpx.AsyncClient(timeout=AUDIO_TIMEOUT_S) as client:
        media = await client.get(
            f"{url}.mp3",
            auth=(settings.twilio_account_sid, settings.twilio_auth_token),
            follow_redirects=True,
        )
    if media.status_code != 200:
        raise HTTPException(status_code=502, detail="twilio would not hand over the recording")
    return Response(content=media.content, media_type="audio/mpeg", headers=PAGE_HEADERS)


@app.post("/voice")
async def voice(call_id: str, form: Annotated[FormData, Depends(twilio_form)]) -> Response:
    if call_id not in CALLS:
        raise HTTPException(status_code=404, detail="unknown call")
    return Response(content=stream_twiml(call_id), media_type="application/xml")


UNANSWERED = ("no-answer", "busy", "failed", "canceled")


def call_for_twilio_sid(form: FormData):
    sid = form.get("CallSid")
    if not sid:
        return None
    return next((call for call in CALLS.values() if call.twilio_sid == sid), None)


@app.post("/voice/status")
async def voice_status(form: Annotated[FormData, Depends(twilio_form)]) -> Response:
    # ponytail: a live call that nobody answers never opens the WebSocket, so `run_call` never
    # runs and no phase emits anything. This callback is the only thing Twilio sends on that
    # path, and the panel needs a `call_ended` to stop reading as a call still dialling.
    status = form.get("CallStatus", "")
    if status not in UNANSWERED:
        return Response(status_code=204)
    call = call_for_twilio_sid(form)
    if call and not any(event["type"] == "call_ended" for event in call.trace):
        call.emit("call_ended", escalated=False, answers={}, reason=status, unanswered=True)
        call.ended_at = call.trace[-1]["at"]
        if STORE is not None:
            try:
                await STORE.save_call(call)
            except Exception as exc:
                call.emit("warning", phase="store", error=repr(exc))
    return Response(status_code=204)


@app.post("/voice/recording")
async def voice_recording(
    background: BackgroundTasks, form: Annotated[FormData, Depends(twilio_form)]
) -> Response:
    url = form.get("RecordingUrl", "")
    if not is_twilio_recording(url):
        raise HTTPException(status_code=400, detail="recording url is not a Twilio url")
    call = call_for_twilio_sid(form)
    if call:
        call.recording_url = url
        call.emit("recording_ready", url=url)
        background.add_task(analysis.run, call, STORE)
    return Response(status_code=204)


def sse_frame(event: dict) -> str:
    return f"id: {event['seq']}\ndata: {json.dumps(event, ensure_ascii=False)}\n\n"


async def event_stream(
    call: Call, snapshot: list[dict], queue: asyncio.Queue, last_id: int
) -> AsyncIterator[str]:
    try:
        yield "retry: 3000\n\n"
        # ponytail: the snapshot and the live events arrive through one `onmessage`, so the client
        # cannot tell them apart on its own and the rail ends up flashing the whole backlog as new.
        # A flag on the frame, not on `call.trace`: the stored event is what `/trace` and the
        # fixtures carry, and this is a fact about the delivery, not about the call.
        for event in snapshot:
            if event["seq"] > last_id:
                yield sse_frame({**event, "replayed": True})
        if any(event["type"] == "call_ended" for event in snapshot):
            return
        while True:
            try:
                event = await asyncio.wait_for(queue.get(), KEEPALIVE_S)
            except TimeoutError:
                # ponytail: a dead subscriber is only reaped on the next keep-alive write.
                # Poll request.is_disconnected() if a call ever has many watchers.
                yield ": keep-alive\n\n"
                continue
            yield sse_frame(event)
            if event["type"] == "call_ended":
                return
    finally:
        call.unsubscribe(queue)


@app.get("/calls/{call_id}/events")
async def call_events(call_id: str, request: Request) -> StreamingResponse:
    call = CALLS.get(call_id)
    if not call:
        raise HTTPException(status_code=404, detail="unknown call")
    snapshot, queue = call.subscribe()
    last_id = int(request.headers.get("last-event-id") or 0)
    return StreamingResponse(
        event_stream(call, snapshot, queue, last_id),
        media_type="text/event-stream",
        headers=SSE_HEADERS,
    )


@app.get("/calls/{call_id}/trace")
async def trace(call_id: str) -> dict:
    call = CALLS.get(call_id)
    if not call:
        raise HTTPException(status_code=404, detail="unknown call")
    return {
        "call_id": call.id,
        "patient": call.patient_name,
        "pack": call.pack.key,
        "memory": call.memory,
        "escalated": call.escalated,
        "answers": call.answers,
        "summary": call.summary,
        "transcript": call.transcript,
        "trace": list(call.trace),
    }


@app.websocket("/media/{call_id}")
async def media(websocket: WebSocket, call_id: str) -> None:
    call = CALLS.get(call_id)
    if not call:
        await websocket.close(code=1008)
        return
    await websocket.accept()
    channel = LiveChannel(websocket, call)
    try:
        await channel.start()
        await run_call(call, channel, GeminiLLM(), STORE, get_settings().silence_s)
    except CallEnded:
        call.emit("call_ended", reason="media-stream-timeout")
    finally:
        await channel.close()


if WEB_DIST.is_dir():

    def page(*parts: str) -> FileResponse:
        return FileResponse(WEB_DIST.joinpath(*parts), headers=PAGE_HEADERS)

    @app.get("/", include_in_schema=False)
    async def landing() -> FileResponse:
        return page("index.html")

    @app.get("/panel", include_in_schema=False)
    async def panel() -> FileResponse:
        return page("panel", "index.html")

    app.mount("/", StaticFiles(directory=WEB_DIST, html=True), name="web")
