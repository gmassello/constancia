from contextlib import asynccontextmanager
from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException, Response, WebSocket
from pydantic import BaseModel, Field
from starlette.datastructures import FormData

from app.calls import CALLS, Call, register
from app.channel import CallEnded, LiveChannel
from app.config import E164, get_settings, is_twilio_recording
from app.llm import GeminiLLM
from app.orchestrator import run_call
from app.packs import get_pack
from app.security import twilio_form
from app.telephony import place_call, stream_twiml


@asynccontextmanager
async def lifespan(app: FastAPI):
    get_settings()
    yield


app = FastAPI(title="constancia", lifespan=lifespan)


class CallRequest(BaseModel):
    patient_name: str
    phone: str = Field(pattern=E164)
    patient_id: str = "seed"
    pack: str = "rehab"
    memory: bool = True


@app.get("/health")
async def health() -> dict:
    return {"status": "ok", "calls": len(CALLS)}


@app.post("/calls")
async def create_call(request: CallRequest) -> dict:
    try:
        pack = get_pack(request.pack)
    except KeyError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    call = register(
        Call(
            patient_id=request.patient_id,
            patient_name=request.patient_name,
            pack=pack,
            memory=request.memory,
        )
    )
    call.twilio_sid = place_call(call.id, request.phone)
    return {"call_id": call.id, "twilio_sid": call.twilio_sid}


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
        await run_call(call, channel, GeminiLLM(), get_settings().silence_s)
    except CallEnded:
        call.emit("call_ended", reason="media stream never started")
    finally:
        await channel.close()
