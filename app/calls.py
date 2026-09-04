import asyncio
import uuid
from collections import deque
from dataclasses import dataclass, field
from datetime import UTC, datetime

from app.packs import VerticalPack

TRACE_BUFFER = 500


def _now() -> str:
    return datetime.now(UTC).isoformat()


@dataclass
class Call:
    patient_id: str
    patient_name: str
    pack: VerticalPack
    memory: bool = True
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    started_at: str = field(default_factory=_now)
    ended_at: str | None = None
    twilio_sid: str | None = None
    recording_url: str | None = None
    transcript: list[dict] = field(default_factory=list)
    answers: dict[str, str] = field(default_factory=dict)
    escalated: dict | None = None
    summary: str | None = None
    facts: list[dict] = field(default_factory=list)
    new_facts: list = field(default_factory=list)
    memory_prompt: str = ""
    trace: deque = field(default_factory=lambda: deque(maxlen=TRACE_BUFFER))
    subscribers: list[asyncio.Queue] = field(default_factory=list)
    _seq: int = 0

    def emit(self, type: str, **data) -> dict:
        self._seq += 1
        event = {"seq": self._seq, "at": _now(), "type": type, **data}
        self.trace.append(event)
        for queue in self.subscribers:
            queue.put_nowait(event)
        return event

    def add_turn(self, speaker: str, text: str, **data) -> int:
        turn_id = len(self.transcript) + 1
        self.transcript.append({"turn_id": turn_id, "speaker": speaker, "text": text, "at": _now()})
        self.emit(f"{speaker}_turn", turn_id=turn_id, text=text, **data)
        return turn_id

    def subscribe(self) -> tuple[list[dict], asyncio.Queue]:
        queue: asyncio.Queue = asyncio.Queue()
        self.subscribers.append(queue)
        return list(self.trace), queue

    def unsubscribe(self, queue: asyncio.Queue) -> None:
        if queue in self.subscribers:
            self.subscribers.remove(queue)

    def history(self) -> list[dict]:
        return [
            {"role": "model" if t["speaker"] == "agent" else "user", "text": t["text"]}
            for t in self.transcript
        ]


CALLS: dict[str, Call] = {}


def register(call: Call) -> Call:
    CALLS[call.id] = call
    return call
