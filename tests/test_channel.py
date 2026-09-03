import asyncio
import json

import pytest

from app import tts
from app.calls import Call
from app.channel import CallEnded, LiveChannel
from app.packs import get_pack

ENV = {
    "GEMINI_API_KEY": "x",
    "ASSEMBLYAI_API_KEY": "x",
    "ELEVENLABS_API_KEY": "x",
    "ELEVENLABS_VOICE_ID": "x",
    "TWILIO_ACCOUNT_SID": "x",
    "TWILIO_AUTH_TOKEN": "x",
    "TWILIO_NUMBER": "+541199999999",
    "PUBLIC_BASE_URL": "https://constancia.example.com",
}

START = json.dumps({"event": "start", "start": {"streamSid": "MZ1"}})


def turn(transcript: str, words: int, final: bool = True) -> dict:
    return {
        "type": "Turn",
        "transcript": transcript,
        "words": [{"text": "w"}] * words,
        "end_of_turn": final,
        "turn_is_formatted": final,
    }


class FakeWS:
    def __init__(self) -> None:
        self.inbox: asyncio.Queue = asyncio.Queue()
        self.sent: list[dict] = []
        self.closed = False

    async def receive_text(self) -> str:
        return await self.inbox.get()

    async def send_text(self, text: str) -> None:
        message = json.loads(text)
        self.sent.append(message)
        if message["event"] == "mark":
            await self.inbox.put(json.dumps({"event": "mark", "mark": message["mark"]}))

    async def close(self) -> None:
        self.closed = True

    def events(self, kind: str) -> list[dict]:
        return [m for m in self.sent if m["event"] == kind]


class FakeSTT:
    def __init__(self) -> None:
        self.queue: asyncio.Queue = asyncio.Queue()
        self.fed = 0
        self.frames = 0
        self.keyterms: list[str] = []

    async def connect(self) -> None:
        return None

    async def feed(self, audio: bytes) -> None:
        self.fed += len(audio)
        self.frames += 1

    async def messages(self):
        while True:
            message = await self.queue.get()
            if message is None:
                return
            yield message

    async def update_keyterms(self, terms: list[str]) -> None:
        self.keyterms = terms

    async def terminate(self) -> None:
        await self.queue.put(None)


@pytest.fixture(autouse=True)
def env(monkeypatch: pytest.MonkeyPatch):
    from app.config import get_settings

    for key, value in ENV.items():
        monkeypatch.setenv(key, value)
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


@pytest.fixture
def speech(monkeypatch: pytest.MonkeyPatch):
    async def stream(text: str):
        for _ in range(10):
            await asyncio.sleep(0.01)
            yield b"\xff" * 800

    monkeypatch.setattr(tts, "stream", stream)


async def started_channel() -> tuple[LiveChannel, FakeWS, FakeSTT]:
    call = Call(patient_id="test", patient_name="Ana", pack=get_pack("rehab"))
    ws, stt = FakeWS(), FakeSTT()
    channel = LiveChannel(ws, call, stt)
    await ws.inbox.put(START)
    await channel.start()
    return channel, ws, stt


async def test_say_streams_ulaw_and_waits_for_the_mark(speech) -> None:
    channel, ws, _ = await started_channel()
    await channel.say("Hola Ana")

    assert len(ws.events("media")) == 10
    assert len(ws.events("mark")) == 1
    assert ws.events("clear") == []
    assert channel.call.transcript[-1]["text"] == "Hola Ana"
    assert channel.call.trace[-1]["interrupted"] is False
    await channel.close()


async def test_barge_in_cancels_playback_and_clears_the_queue(speech) -> None:
    channel, ws, stt = await started_channel()

    async def interrupt() -> None:
        await asyncio.sleep(0.03)
        await stt.queue.put(turn("Pará, te interrumpo", words=3))

    await asyncio.gather(channel.say("Una pregunta bien larga"), interrupt())

    assert ws.events("clear")
    assert len(ws.events("media")) < 10
    assert channel.call.trace[-1]["interrupted"] is True
    assert await channel.listen(0.5) == "Pará, te interrumpo"
    await channel.close()


async def test_partial_turns_do_not_reach_listen(speech) -> None:
    channel, _, stt = await started_channel()
    await stt.queue.put(turn("parcial", words=1, final=False))

    assert await channel.listen(0.05) is None
    await channel.close()


async def test_inbound_audio_is_batched_into_100ms_frames() -> None:
    import base64

    channel, ws, stt = await started_channel()
    for _ in range(5):
        payload = base64.b64encode(b"\xff" * 160).decode()
        await ws.inbox.put(json.dumps({"event": "media", "media": {"payload": payload}}))
    await asyncio.sleep(0.05)

    assert stt.frames == 1
    assert stt.fed == 800
    await channel.close()


async def test_hangup_surfaces_as_call_ended() -> None:
    channel, ws, _ = await started_channel()
    await ws.inbox.put(json.dumps({"event": "stop"}))
    await asyncio.sleep(0.05)

    with pytest.raises(CallEnded):
        await channel.listen(0.05)
    await channel.close()


async def test_start_times_out_without_a_twilio_stream(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("app.channel.START_TIMEOUT_S", 0.05)
    call = Call(patient_id="test", patient_name="Ana", pack=get_pack("rehab"))
    channel = LiveChannel(FakeWS(), call, FakeSTT())

    with pytest.raises(CallEnded):
        await channel.start()
    await channel.close()
