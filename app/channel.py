import asyncio
import base64
import contextlib
import json

from app import tts
from app.calls import Call
from app.config import get_settings
from app.stt import StreamingSTT

FRAME_BYTES = 800
BYTES_PER_SECOND = 8000
MARK_GRACE_S = 2.0
START_TIMEOUT_S = 10.0
LOGGED_FRAMES = 3


class CallEnded(Exception):
    pass


class ScriptedPatient:
    def __init__(self, call: Call, answers: list[str | None], delay_s: float = 0.0) -> None:
        self.call = call
        self.answers = list(answers)
        self.delay_s = delay_s
        self.said: list[str] = []
        self.keyterms: list[str] = []
        self.closed = False

    async def _pace(self) -> None:
        if self.delay_s:
            await asyncio.sleep(self.delay_s)

    async def say(self, text: str) -> None:
        if self.closed:
            raise CallEnded
        await self._pace()
        self.said.append(text)
        self.call.add_turn("agent", text, interrupted=False)

    async def listen(self, timeout: float) -> str | None:
        if self.closed:
            raise CallEnded
        if not self.answers:
            raise CallEnded
        await self._pace()
        answer = self.answers.pop(0)
        if answer is None:
            return None
        self.call.add_turn("patient", answer)
        return answer

    async def set_keyterms(self, terms: list[str]) -> None:
        self.keyterms = terms

    async def close(self) -> None:
        self.closed = True


class LiveChannel:
    def __init__(self, websocket, call: Call, stt: StreamingSTT | None = None) -> None:
        self.ws = websocket
        self.call = call
        self.stt = stt or StreamingSTT()
        self.stream_sid: str | None = None
        self.started = asyncio.Event()
        self.hung_up = asyncio.Event()
        self.turns: asyncio.Queue = asyncio.Queue()
        self.barge = asyncio.Event()
        self.mark_event = asyncio.Event()
        self.speaking = False
        self.tts_task: asyncio.Task | None = None
        self.tasks: list[asyncio.Task] = []
        self.closed = False
        self.barge_min_words = get_settings().barge_min_words

    async def start(self) -> None:
        await self.stt.connect()
        self.tasks = [
            asyncio.create_task(self._twilio_reader()),
            asyncio.create_task(self._aai_reader()),
        ]
        try:
            await asyncio.wait_for(self.started.wait(), START_TIMEOUT_S)
        except TimeoutError as exc:
            self.call.emit("warning", phase="channel", error="twilio stream never started")
            raise CallEnded from exc

    def _hang_up(self) -> None:
        if not self.hung_up.is_set():
            self.hung_up.set()
            self.turns.put_nowait(None)

    async def _send(self, message: dict) -> None:
        await self.ws.send_text(json.dumps(message))

    async def _twilio_reader(self) -> None:
        buffer = bytearray()
        seen = 0
        try:
            while True:
                message = json.loads(await self.ws.receive_text())
                event = message.get("event")
                if seen < LOGGED_FRAMES:
                    seen += 1
                    self.call.emit("twilio_frame", event=event)
                if event == "start":
                    self.stream_sid = message["start"]["streamSid"]
                    self.started.set()
                elif event == "media":
                    buffer += base64.b64decode(message["media"]["payload"])
                    while len(buffer) >= FRAME_BYTES:
                        await self.stt.feed(bytes(buffer[:FRAME_BYTES]))
                        del buffer[:FRAME_BYTES]
                elif event == "mark":
                    self.mark_event.set()
                elif event == "stop":
                    break
        except asyncio.CancelledError:
            raise
        except Exception as exc:
            self.call.emit("warning", phase="twilio_reader", error=repr(exc))
        finally:
            self._hang_up()

    async def _aai_reader(self) -> None:
        try:
            async for message in self.stt.messages():
                if message.get("type") != "Turn":
                    continue
                transcript = (message.get("transcript") or "").strip()
                if not transcript:
                    continue
                words = message.get("words") or []
                if self.speaking and self.barge_min_words and len(words) >= self.barge_min_words:
                    self.barge.set()
                if message.get("end_of_turn") and message.get("turn_is_formatted"):
                    self.turns.put_nowait(transcript)
        except asyncio.CancelledError:
            raise
        except Exception as exc:
            self.call.emit("warning", phase="stt_reader", error=repr(exc))
        finally:
            self._hang_up()

    async def _stream_tts(self, text: str) -> None:
        sent = 0
        async for chunk in tts.stream(text):
            if self.hung_up.is_set():
                return
            await self._send(
                {
                    "event": "media",
                    "streamSid": self.stream_sid,
                    "media": {"payload": base64.b64encode(chunk).decode()},
                }
            )
            sent += len(chunk)
        await self._send(
            {"event": "mark", "streamSid": self.stream_sid, "mark": {"name": "utterance"}}
        )
        with contextlib.suppress(TimeoutError):
            await asyncio.wait_for(self.mark_event.wait(), sent / BYTES_PER_SECOND + MARK_GRACE_S)

    def _drain_turns(self) -> None:
        while not self.turns.empty():
            item = self.turns.get_nowait()
            if item is None:
                self.turns.put_nowait(None)
                return

    async def say(self, text: str) -> None:
        if self.hung_up.is_set():
            raise CallEnded
        self._drain_turns()
        self.barge.clear()
        self.mark_event.clear()
        self.speaking = True
        self.tts_task = asyncio.create_task(self._stream_tts(text))
        watchers = [
            asyncio.create_task(self.barge.wait()),
            asyncio.create_task(self.hung_up.wait()),
        ]
        done, pending = await asyncio.wait(
            [self.tts_task, *watchers], return_when=asyncio.FIRST_COMPLETED
        )
        interrupted = self.tts_task not in done and self.barge.is_set()
        for task in pending:
            task.cancel()
        await asyncio.gather(*pending, return_exceptions=True)
        self.speaking = False
        if interrupted:
            await self._send({"event": "clear", "streamSid": self.stream_sid})
        elif self.tts_task in done and self.tts_task.exception():
            self.call.emit("warning", phase="tts", error=repr(self.tts_task.exception()))
        self.call.add_turn("agent", text, interrupted=interrupted)

    async def listen(self, timeout: float) -> str | None:
        if self.hung_up.is_set():
            raise CallEnded
        try:
            item = await asyncio.wait_for(self.turns.get(), timeout)
        except TimeoutError:
            return None
        if item is None:
            raise CallEnded
        self.call.add_turn("patient", item)
        return item

    async def set_keyterms(self, terms: list[str]) -> None:
        await self.stt.update_keyterms(terms)

    async def close(self) -> None:
        if self.closed:
            return
        self.closed = True
        self._hang_up()
        if self.tts_task and not self.tts_task.done():
            self.tts_task.cancel()
            await asyncio.gather(self.tts_task, return_exceptions=True)
        await self.stt.terminate()
        for task in self.tasks:
            task.cancel()
        await asyncio.gather(*self.tasks, return_exceptions=True)
        with contextlib.suppress(Exception):
            await self.ws.close()
