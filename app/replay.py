import asyncio
import json
from datetime import datetime
from pathlib import Path

from app.calls import Call, _now
from app.channel import ScriptedPatient
from app.config import settings_or_none
from app.llm import GeminiLLM, ScriptedLLM
from app.orchestrator import run_call

ROOT = Path(__file__).resolve().parent.parent
SCRIPTS_PATH = ROOT / "seed" / "scripts.json"
FIXTURES = ROOT / "seed" / "replay"
TURN_DELAY_S = 1.2
MAX_GAP_S = 3.0


def scripts() -> dict:
    return json.loads(SCRIPTS_PATH.read_text(encoding="utf-8"))


def extraction(script: dict, current_facts: list[dict]) -> str:
    by_term = {fact["term"]: str(fact["id"]) for fact in current_facts}
    return json.dumps(
        {"facts": [{**f, "supersedes": by_term.get(f["term"])} for f in script["facts"]]},
        ensure_ascii=False,
    )


def build_llm(script: dict, current_facts: list[dict]):
    settings = settings_or_none()
    if settings and settings.gemini_api_key:
        return GeminiLLM()
    return ScriptedLLM(structured_replies=[extraction(script, current_facts)])


async def run_scripted(call: Call, store, name: str | None = None, delay_s=TURN_DELAY_S) -> Call:
    available = scripts()
    facts = await store.current_facts(call.patient_id) if store and call.memory else []
    name = name or ("week2" if facts else "week1")
    script = available[name]
    channel = ScriptedPatient(call, list(script["answers"]), delay_s=delay_s)
    return await run_call(call, channel, build_llm(script, facts), store, silence_s=0.1)


def export(call: Call) -> dict:
    events = list(call.trace)
    start = events[0]["at"] if events else _now()
    base = _seconds(start)
    return {
        "call": {
            "patient_id": call.patient_id,
            "patient_name": call.patient_name,
            "pack": call.pack.key,
            "memory": call.memory,
        },
        "events": [
            {
                "t": round(_seconds(event["at"]) - base, 3),
                **{k: v for k, v in event.items() if k not in ("at", "seq")},
            }
            for event in events
        ],
    }


def _seconds(at: str) -> float:
    return datetime.fromisoformat(at).timestamp()


def load_fixture(name: str) -> dict:
    path = FIXTURES / f"{name}.json"
    if not path.is_file():
        raise FileNotFoundError(f"no recording named {name}")
    return json.loads(path.read_text(encoding="utf-8"))


async def run_recorded(call: Call, name: str, speed: float = 1.0) -> Call:
    recording = load_fixture(name)
    previous = 0.0
    for event in recording["events"]:
        gap = min(MAX_GAP_S, max(0.0, event["t"] - previous)) / speed
        previous = event["t"]
        if gap:
            await asyncio.sleep(gap)
        payload = {k: v for k, v in event.items() if k not in ("t", "type")}
        if event["type"] in ("agent_turn", "patient_turn"):
            call.transcript.append(
                {
                    "turn_id": payload["turn_id"],
                    "speaker": event["type"].removesuffix("_turn"),
                    "text": payload["text"],
                    "at": _now(),
                }
            )
        call.emit(event["type"], **payload)
    return call
