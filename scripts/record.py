import asyncio
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# ponytail: recorded takes must be byte-identical every run. Four things would break that and all
# four are pinned: the two keys that would reach a network are blanked here — Gemini, which
# build_llm would pick, and the gateway, which app/commitments.recall would ask whenever a scripted
# promise misses the action vocabulary — `t` is quantised in app/replay.export, and FakeStore mints
# fact ids from a counter. The mirror of scripts/demo.py, which fills keys in.
# `make fixtures && git diff --exit-code seed/replay/` is the check.
os.environ["GEMINI_API_KEY"] = ""
os.environ["AI_GATEWAY_API_KEY"] = ""

from app import replay  # noqa: E402
from app.calls import Call  # noqa: E402
from app.memory import load_seed  # noqa: E402
from app.packs import get_pack  # noqa: E402

PATIENT_ID = "8c9d0e1f-2a3b-4c5d-6e7f-8091a2b3c4d5"
TAKES = (
    ("week1", "week1", False),
    ("week2-off", "week2-off", False),
    ("week2-on", "week2", True),
    ("alarm", "alarm", True),
)


async def record(name: str, script: str, memory: bool) -> int:
    store = load_seed()
    call = Call(
        patient_id=PATIENT_ID,
        patient_name="Ana",
        pack=get_pack("rehab"),
        memory=memory,
    )
    await replay.run_scripted(call, store, script)
    path = replay.FIXTURES / f"{name}.json"
    path.write_text(
        json.dumps(replay.export(call), ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    return len(call.trace)


async def main() -> None:
    replay.FIXTURES.mkdir(parents=True, exist_ok=True)
    for name, script, memory in TAKES:
        events = await record(name, script, memory)
        print(f"{name}: {events} events")


if __name__ == "__main__":
    asyncio.run(main())
