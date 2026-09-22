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


def media(audio: bytes) -> str:
    import base64

    return json.dumps({"event": "media", "media": {"payload": base64.b64encode(audio).decode()}})


def turn(transcript: str, words: int, final: bool = True, start_ms: int = 0) -> dict:
    return {
        "type": "Turn",
        "transcript": transcript,
        "words": [
            {"text": "w", "start": start_ms + i * 80, "end": start_ms + i * 80 + 80}
            for i in range(words)
        ],
        "end_of_turn": final,
        "turn_is_formatted": final,
    }


class FakeWS:
    def __init__(self) -> None:
        self.inbox: asyncio.Queue = asyncio.Queue()
        self.sent: list[dict] = []
        self.closed = False
        self.gone = False

    async def receive_text(self) -> str:
        return await self.inbox.get()

    async def send_text(self, text: str) -> None:
        if self.gone:
            raise ConnectionError("twilio closed its side")
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
        self.pending: list[dict] = []
        self.finish_delay = 0.0

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

    async def finish(self) -> None:
        await asyncio.sleep(self.finish_delay)
        for message in self.pending:
            await self.queue.put(message)
        await self.queue.put(None)

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


@pytest.fixture
def mute(monkeypatch: pytest.MonkeyPatch):
    async def stream(text: str):
        raise RuntimeError("elevenlabs said 401")
        yield b""

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
    await channel.say("Hi Ana")

    assert len(ws.events("media")) == 10
    assert len(ws.events("mark")) == 1
    assert ws.events("clear") == []
    assert channel.call.transcript[-1]["text"] == "Hi Ana"
    assert channel.call.trace[-1]["interrupted"] is False
    await channel.close()


async def test_barge_in_cancels_playback_and_clears_the_queue(speech) -> None:
    channel, ws, stt = await started_channel()

    async def interrupt() -> None:
        await asyncio.sleep(0.03)
        await stt.queue.put(turn("Wait, let me interrupt", words=3))

    await asyncio.gather(channel.say("A really long question"), interrupt())

    assert ws.events("clear")
    assert len(ws.events("media")) < 10
    assert channel.call.trace[-1]["interrupted"] is True
    assert await channel.listen(0.5) == "Wait, let me interrupt"
    await channel.close()


async def test_words_spoken_before_the_agent_started_are_not_a_barge_in(speech) -> None:
    channel, ws, stt = await started_channel()
    for _ in range(20):
        await ws.inbox.put(media(b"\xff" * 800))
    while channel.fed_ms < 2000:
        await asyncio.sleep(0.01)

    async def late_transcript() -> None:
        await asyncio.sleep(0.03)
        await stt.queue.put(turn("this is Ana", words=3, start_ms=500))

    await asyncio.gather(channel.say("A really long question"), late_transcript())

    assert channel.call.trace[-1]["interrupted"] is False
    assert ws.events("clear") == []
    assert len(ws.events("media")) == 10
    await channel.close()


async def test_words_spoken_over_the_agent_still_barge_in(speech) -> None:
    channel, ws, stt = await started_channel()
    for _ in range(20):
        await ws.inbox.put(media(b"\xff" * 800))
    while channel.fed_ms < 2000:
        await asyncio.sleep(0.01)

    async def interrupt() -> None:
        await asyncio.sleep(0.03)
        await stt.queue.put(turn("wait, stop", words=3, start_ms=channel.fed_ms))

    await asyncio.gather(channel.say("A really long question"), interrupt())

    assert channel.call.trace[-1]["interrupted"] is True
    assert ws.events("clear")
    await channel.close()


async def test_a_turn_that_lands_mid_question_is_not_served_as_its_answer(speech) -> None:
    channel, _, stt = await started_channel()

    async def tail_of_the_previous_answer() -> None:
        await asyncio.sleep(0.03)
        await stt.queue.put(turn("because I had a lot of work", words=1, start_ms=0))

    await asyncio.gather(channel.say("Any new discomfort?"), tail_of_the_previous_answer())

    assert channel.call.trace[-1]["interrupted"] is False
    assert await channel.listen(0.05) is None
    await channel.close()


async def test_a_turn_the_tts_never_spoke_is_not_written_into_the_transcript(mute) -> None:
    channel, ws, _ = await started_channel()
    await channel.say("Hi Ana")

    assert ws.events("media") == []
    assert [t["speaker"] for t in channel.call.transcript] == []
    warnings = [e for e in channel.call.trace if e["type"] == "warning"]
    assert [w["phase"] for w in warnings] == ["tts"]
    await channel.close()


async def test_partial_turns_do_not_reach_listen(speech) -> None:
    channel, _, stt = await started_channel()
    await stt.queue.put(turn("partial", words=1, final=False))

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


async def test_a_turn_that_lands_mid_question_still_reaches_the_transcript_and_the_guard(
    speech,
) -> None:
    channel, _, stt = await started_channel()

    async def tail_of_the_previous_answer() -> None:
        await asyncio.sleep(0.03)
        await stt.queue.put(turn("and I fell on Tuesday", words=1, start_ms=0))

    await asyncio.gather(channel.say("Any new discomfort?"), tail_of_the_previous_answer())

    assert await channel.listen(0.05) is None
    assert channel.call.transcript[0]["speaker"] == "patient"
    assert channel.call.transcript[0]["text"] == "and I fell on Tuesday"
    assert channel.take_dropped() == ["and I fell on Tuesday"]
    assert channel.take_dropped() == []
    assert channel.call.transcript[0]["heard"] is False
    assert channel.call.transcript[1]["interrupted"] is False
    await channel.close()


async def drive_to_the_goodbye(flag: str, words: int, partial: bool) -> tuple[Call, LiveChannel]:
    from app import orchestrator
    from app.llm import ScriptedLLM

    channel, _, stt = await started_channel()
    call = channel.call

    async def patient() -> None:
        for _ in range(len(call.pack.questions)):
            await asyncio.sleep(0.04)
            await stt.queue.put(turn("all fine thanks", words=3))
        await asyncio.sleep(0.04)
        await stt.queue.put(turn(flag, words=words, final=not partial))
        if partial:
            await asyncio.sleep(0.04)
            await stt.queue.put(turn(flag, words=words))

    await asyncio.gather(orchestrator.converse(call, channel, ScriptedLLM(), None, 1.0), patient())
    return call, channel


@pytest.mark.parametrize(
    ("flag", "words", "partial"), [("fell", 1, False), ("I had a fall yesterday", 5, True)]
)
async def test_a_red_flag_over_the_goodbye_still_reaches_the_guard(
    speech, flag: str, words: int, partial: bool
) -> None:
    call, channel = await drive_to_the_goodbye(flag, words, partial)

    assert call.escalated is not None
    assert call.escalated["rule"] == "fall"
    assert flag in [t["text"] for t in call.transcript if t["speaker"] == "patient"]
    assert channel.turns.empty()
    await channel.close()


async def test_a_turn_still_finalizing_at_the_hangup_reaches_the_transcript() -> None:
    channel, ws, stt = await started_channel()
    stt.pending = [turn("I fell in the shower yesterday.", words=5)]
    await stt.queue.put(turn("I fell", words=2, final=False))
    await ws.inbox.put(json.dumps({"event": "stop"}))

    assert await channel.listen(1.0) == "I fell in the shower yesterday."
    with pytest.raises(CallEnded):
        await channel.listen(0.05)
    await channel.close()


async def test_a_hangup_still_runs_the_guard_over_turns_the_agent_talked_over(speech) -> None:
    from app import orchestrator
    from app.llm import ScriptedLLM

    channel, ws, stt = await started_channel()
    call = channel.call

    async def patient() -> None:
        while not any(e.get("phase") == "converse" for e in call.trace):
            await asyncio.sleep(0.01)
        await asyncio.sleep(0.03)
        await stt.queue.put(turn("I fell in the shower yesterday", words=1, start_ms=0))
        await asyncio.sleep(0.15)
        await ws.inbox.put(json.dumps({"event": "stop"}))

    await asyncio.gather(orchestrator.run_call(call, channel, ScriptedLLM(), None, 0.2), patient())

    assert call.escalated is not None
    assert call.escalated["rule"] == "fall"
    assert "guard_hit" in [e["type"] for e in call.trace]
    assert "patient_hung_up" in [e["type"] for e in call.trace]


async def test_a_hangup_mid_question_sends_nothing_to_the_closed_twilio_socket(speech) -> None:
    from app import orchestrator
    from app.llm import ScriptedLLM

    channel, ws, stt = await started_channel()
    call = channel.call
    stt.finish_delay = 0.3
    stt.pending = [turn("I fell yesterday", words=3, start_ms=10_000)]

    async def patient() -> None:
        while not any(e.get("phase") == "converse" for e in call.trace):
            await asyncio.sleep(0.01)
        await asyncio.sleep(0.03)
        ws.gone = True
        await ws.inbox.put(json.dumps({"event": "stop"}))
        await asyncio.sleep(0.05)
        await stt.queue.put(turn("I fell", words=3, final=False, start_ms=10_000))

    await asyncio.gather(orchestrator.run_call(call, channel, ScriptedLLM(), None, 0.2), patient())
    kinds = [e["type"] for e in call.trace]

    assert call.escalated is not None
    assert call.escalated["rule"] == "fall"
    assert "phase_failed" not in kinds
    assert "warning" not in kinds
    assert "summary" in kinds


async def test_a_failed_converse_still_runs_the_guard_and_closes_the_call(speech) -> None:
    from app import orchestrator
    from app.llm import ScriptedLLM

    channel, _, stt = await started_channel()
    call = channel.call

    class FailingLLM(ScriptedLLM):
        async def reply(self, system, history, emit=None):
            if len(self.prompts) == 2:
                await stt.queue.put(turn("oh and I fell yesterday", words=1))
                await asyncio.sleep(0.02)
                raise RuntimeError("gemini gave up")
            return await super().reply(system, history, emit)

    async def patient() -> None:
        for _ in range(2):
            while not channel.speaking:
                await asyncio.sleep(0.01)
            while channel.speaking:
                await asyncio.sleep(0.01)
            await stt.queue.put(turn("all fine thanks", words=3))

    await asyncio.gather(orchestrator.run_call(call, channel, FailingLLM(), None, 1.0), patient())

    assert "phase_failed" in [e["type"] for e in call.trace]
    assert call.escalated is not None
    assert call.escalated["rule"] == "fall"
    assert call.ended_at is not None
