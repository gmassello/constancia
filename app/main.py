import asyncio
import json
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Annotated, Literal
from uuid import UUID

from fastapi import BackgroundTasks, Depends, FastAPI, HTTPException, Request, Response, WebSocket
from fastapi.responses import StreamingResponse
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
DEFAULT_FIXTURE = "week2-on"
PANEL_DIST = Path(__file__).resolve().parent.parent / "panel" / "dist"


@asynccontextmanager
async def lifespan(app: FastAPI):
    global STORE
    settings = settings_or_none()
    STORE = MemoryStore() if settings and settings.database_url else load_seed()
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
    phone = request.phone or (row or {}).get("phone_e164")
    if not name or (request.mode == "live" and not phone):
        raise HTTPException(status_code=400, detail="unknown patient: send patient_name and phone")
    try:
        pack = get_pack(request.pack or (row or {}).get("program_type") or "rehab")
    except KeyError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    call = register(
        Call(
            patient_id=patient_id,
            patient_name=name,
            pack=pack,
            memory=request.memory,
        )
    )
    if request.mode == "live":
        if not settings_or_none():
            raise HTTPException(status_code=503, detail="live mode needs credentials")
        call.twilio_sid = place_call(call.id, phone)
    elif request.mode == "scripted":
        call.task = asyncio.create_task(replay.run_scripted(call, STORE, request.script))
    else:
        try:
            replay.load_fixture(request.script or DEFAULT_FIXTURE)
        except FileNotFoundError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        call.task = asyncio.create_task(
            replay.run_recorded(call, request.script or DEFAULT_FIXTURE)
        )
    return {"call_id": call.id, "mode": request.mode, "twilio_sid": call.twilio_sid}


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
    return queries.weekly(await STORE.chain(str(patient_id)), term)


@app.get("/patients/{patient_id}/facts")
async def patient_facts(patient_id: UUID) -> dict:
    return {"patient_id": str(patient_id), "facts": await STORE.chain(str(patient_id))}


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


@app.post("/voice")
async def voice(call_id: str, form: Annotated[FormData, Depends(twilio_form)]) -> Response:
    if call_id not in CALLS:
        raise HTTPException(status_code=404, detail="unknown call")
    return Response(content=stream_twiml(call_id), media_type="application/xml")


@app.post("/voice/status")
async def voice_status(form: Annotated[FormData, Depends(twilio_form)]) -> Response:
    return Response(status_code=204)


@app.post("/voice/recording")
async def voice_recording(
    background: BackgroundTasks, form: Annotated[FormData, Depends(twilio_form)]
) -> Response:
    url = form.get("RecordingUrl", "")
    if not is_twilio_recording(url):
        raise HTTPException(status_code=400, detail="recording url is not a Twilio url")
    call = next((c for c in CALLS.values() if c.twilio_sid == form.get("CallSid")), None)
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
        for event in snapshot:
            if event["seq"] > last_id:
                yield sse_frame(event)
        if snapshot and snapshot[-1]["type"] == "call_ended":
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
        call.emit("call_ended", reason="media stream never started")
    finally:
        await channel.close()


if PANEL_DIST.is_dir():
    app.mount("/", StaticFiles(directory=PANEL_DIST, html=True), name="panel")
