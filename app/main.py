from contextlib import asynccontextmanager
from typing import Annotated
from uuid import UUID

from fastapi import Depends, FastAPI, HTTPException, Response, WebSocket
from pydantic import BaseModel, Field
from starlette.datastructures import FormData

from app import db
from app.calls import CALLS, Call, register
from app.channel import CallEnded, LiveChannel
from app.config import E164, get_settings, is_twilio_recording
from app.llm import GeminiLLM
from app.memory import MemoryStore
from app.orchestrator import run_call
from app.packs import get_pack
from app.security import twilio_form
from app.telephony import place_call, stream_twiml

STORE: MemoryStore | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global STORE
    if get_settings().database_url:
        STORE = MemoryStore()
    yield
    STORE = None
    await db.close_pool()


app = FastAPI(title="constancia", lifespan=lifespan)


class CallRequest(BaseModel):
    patient_id: UUID
    patient_name: str | None = None
    phone: str | None = Field(default=None, pattern=E164)
    pack: str | None = None
    memory: bool = True


@app.get("/health")
async def health() -> dict:
    return {"status": "ok", "calls": len(CALLS)}


@app.post("/calls")
async def create_call(request: CallRequest) -> dict:
    patient_id = str(request.patient_id)
    row = await STORE.patient(patient_id) if STORE else None
    name = request.patient_name or (row or {}).get("name")
    phone = request.phone or (row or {}).get("phone_e164")
    if not name or not phone:
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
    call.twilio_sid = place_call(call.id, phone)
    return {"call_id": call.id, "twilio_sid": call.twilio_sid}


@app.get("/patients/{patient_id}/facts")
async def patient_facts(patient_id: UUID) -> dict:
    if not STORE:
        raise HTTPException(status_code=503, detail="no memory store configured")
    return {"patient_id": str(patient_id), "facts": await STORE.chain(str(patient_id))}


@app.post("/voice")
async def voice(call_id: str, form: Annotated[FormData, Depends(twilio_form)]) -> Response:
    if call_id not in CALLS:
        raise HTTPException(status_code=404, detail="unknown call")
    return Response(content=stream_twiml(call_id), media_type="application/xml")


@app.post("/voice/status")
async def voice_status(form: Annotated[FormData, Depends(twilio_form)]) -> Response:
    return Response(status_code=204)


@app.post("/voice/recording")
async def voice_recording(form: Annotated[FormData, Depends(twilio_form)]) -> Response:
    url = form.get("RecordingUrl", "")
    if not is_twilio_recording(url):
        raise HTTPException(status_code=400, detail="recording url is not a Twilio url")
    call = next((c for c in CALLS.values() if c.twilio_sid == form.get("CallSid")), None)
    if call:
        call.recording_url = url
        call.emit("recording_ready", url=url)
    return Response(status_code=204)


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
