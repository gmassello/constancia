import asyncio
import base64
import contextlib
import json

from app import numbers, tts
from app.calls import Call
from app.config import get_settings
from app.stt import StreamingSTT

FRAME_BYTES = 800
BYTES_PER_SECOND = 8000
FRAME_MS = FRAME_BYTES * 1000 // BYTES_PER_SECOND
MARK_GRACE_S = 2.0
START_TIMEOUT_S = 10.0
FLUSH_S = 2.0
LOGGED_FRAMES = 3


class CallEnded(Exception):
    pass


def spoken(answer) -> tuple[str, list[str]]:
    if isinstance(answer, dict):
        return answer["text"], list(answer.get("low_conf") or [])
    return answer, []


class ScriptedPatient:
    def __init__(self, call: Call, answers: list, delay_s: float = 0.0) -> None:
        self.call = call
        self.answers = list(answers)
        self.delay_s = delay_s
        self.said: list[str] = []
        self.keyterms: list[str] = []
        self.closed = False

    def take_dropped(self) -> list[str]:
        return []

    async def _pace(self) -> None:
        if self.delay_s:
            await asyncio.sleep(self.delay_s)

    async def say(self, text: str) -> bool:
        if self.closed:
            raise CallEnded
        await self._pace()
        self.said.append(text)
        self.call.add_turn("agent", text, interrupted=False)
        return False

    async def listen(self, timeout: float) -> str | None:
        if self.closed:
            raise CallEnded
        if not self.answers:
            raise CallEnded
        await self._pace()
        answer = self.answers.pop(0)
        if answer is None:
            return None
        text, low_conf = spoken(answer)
        self.call.add_turn("patient", text, **({"low_conf": low_conf} if low_conf else {}))
        return text

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
        self.dropped: list[str] = []
        self.barge = asyncio.Event()
        self.mark_event = asyncio.Event()
        self.speaking = False
        self.fed_ms = 0
        self.speech_from_ms = 0
        self.tts_task: asyncio.Task | None = None
        self.tasks: list[asyncio.Task] = []
        self.closed = False
        self.stopped = False
        self.barge_min_words = get_settings().barge_min_words
        self.confidence_floor = get_settings().stt_confidence_floor

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
        if self.stopped:
            return
        try:
            await self.ws.send_text(json.dumps(message))
        except (ConnectionError, RuntimeError):
            # ponytail: the far end is gone, so stop writing, but leave the hangup to the reader.
            # Its `stop` branch flushes the recogniser first, and a red flag the patient said in
            # that window still has to reach the guard. Ending the call here skips the flush.
            self.stopped = True

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
                        self.fed_ms += FRAME_MS
                elif event == "mark":
                    self.mark_event.set()
                elif event == "stop":
                    self.stopped = True
                    await self.stt.finish()
                    await asyncio.wait(self.tasks[1:], timeout=FLUSH_S)
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
                spoken_over_agent = words and words[0].get("start", 0) >= self.speech_from_ms
                if (
                    self.speaking
                    and spoken_over_agent
                    and self.barge_min_words
                    and len(words) >= self.barge_min_words
                ):
                    self.barge.set()
                if message.get("end_of_turn") and message.get("turn_is_formatted"):
                    self.turns.put_nowait((transcript, self._doubtful(words)))
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

    def _doubtful(self, words: list[dict]) -> list[str]:
        # ponytail: a word with no `confidence` counts as certain, so a Turn frame that does not
        # carry the field leaves the re-ask switched off instead of firing on every number. That
        # is the degraded mode until a real call confirms v3 sends it.
        if not self.confidence_floor:
            return []
        return [
            str(word.get("text", ""))
            for word in words
            if numbers.is_number(str(word.get("text", "")))
            and float(word.get("confidence", 1.0)) < self.confidence_floor
        ]

    def _drain_turns(self) -> None:
        while not self.turns.empty():
            item = self.turns.get_nowait()
            if item is None:
                self.turns.put_nowait(None)
                return
            text, low_conf = item
            self.call.add_turn(
                "patient", text, heard=False, **({"low_conf": low_conf} if low_conf else {})
            )
            self.dropped.append(text)

    def take_dropped(self) -> list[str]:
        self._drain_turns()
        dropped, self.dropped = self.dropped, []
        return dropped

    async def say(self, text: str) -> bool:
        if self.hung_up.is_set():
            raise CallEnded
        if self.stopped:
            with contextlib.suppress(TimeoutError):
                await asyncio.wait_for(self.hung_up.wait(), FLUSH_S)
            raise CallEnded
        self._drain_turns()
        self.barge.clear()
        self.mark_event.clear()
        # ponytail: the caller's earlier audio keeps finalising while the agent talks. Two defences,
        # because it arrives by two routes: word `start` (milliseconds of caller audio, against how
        # much we have fed) keeps it from counting as an interruption, and the drain below keeps a
        # turn that landed mid-question from being served as the answer to it. An interrupted turn
        # is not drained: there the queued words are the interruption. A drained turn is written to
        # the transcript with `heard=False` — the flag reaches the row, not only the event — and
        # held in `dropped` for the guard, because it is the
        # attribution that is wrong, not the words: dropping them loses clinical content and any
        # red flag inside it. An interrupted turn stays queued, so `take_dropped` drains again
        # before it answers: the guard reads the queue, not only what a `say` happened to drain.
        self.speech_from_ms = self.fed_ms
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
        if not interrupted:
            self._drain_turns()
        spoken = True
        if interrupted:
            await self._send({"event": "clear", "streamSid": self.stream_sid})
        elif self.tts_task in done and self.tts_task.exception():
            self.call.emit("warning", phase="tts", error=repr(self.tts_task.exception()))
            spoken = False
        # ponytail: a turn the patient never heard is dropped rather than recorded, because the
        # transcript is what the professional reads and what `summarize` writes over. The `warning`
        # in the trace is the only evidence, which costs the panel the text of the question. Record
        # it with a `spoken=False` flag instead once anything downstream is ready to read one.
        if spoken:
            self.call.add_turn("agent", text, interrupted=interrupted)
        return interrupted

    async def listen(self, timeout: float) -> str | None:
        if self.hung_up.is_set():
            raise CallEnded
        try:
            item = await asyncio.wait_for(self.turns.get(), timeout)
        except TimeoutError:
            return None
        if item is None:
            raise CallEnded
        text, low_conf = item
        self.call.add_turn("patient", text, **({"low_conf": low_conf} if low_conf else {}))
        return text

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
