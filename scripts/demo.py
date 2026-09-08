import asyncio
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app import replay  # noqa: E402
from app.calls import Call, register  # noqa: E402
from app.memory import load_seed  # noqa: E402
from app.packs import get_pack  # noqa: E402

PATIENT_ID = "8c9d0e1f-2a3b-4c5d-6e7f-8091a2b3c4d5"

PLACEHOLDERS = {
    "ASSEMBLYAI_API_KEY": "unused-in-demo",
    "ELEVENLABS_API_KEY": "unused-in-demo",
    "ELEVENLABS_VOICE_ID": "unused-in-demo",
    "TWILIO_ACCOUNT_SID": "unused-in-demo",
    "TWILIO_AUTH_TOKEN": "unused-in-demo",
    "TWILIO_NUMBER": "+541100000000",
    "PUBLIC_BASE_URL": "http://localhost:8000",
}


async def main() -> None:
    with_memory = os.environ.get("MEMORY", "").lower() in ("on", "1", "true")
    if os.environ.get("GEMINI_API_KEY"):
        for key, value in PLACEHOLDERS.items():
            os.environ.setdefault(key, value)

    store = load_seed() if with_memory else None
    call = register(
        Call(
            patient_id=PATIENT_ID,
            patient_name="Ana",
            pack=get_pack("rehab"),
            memory=with_memory,
        )
    )
    await replay.run_scripted(call, store, delay_s=0.0)

    for turn in call.transcript:
        who = "agente " if turn["speaker"] == "agent" else "paciente"
        print(f"{turn['turn_id']:>2} {who}  {turn['text']}")
    print()
    for event in call.trace:
        print(json.dumps(event, ensure_ascii=False))
    print()
    print("answers:", json.dumps(call.answers, ensure_ascii=False))
    print("escalated:", call.escalated)
    print("summary:", call.summary)


if __name__ == "__main__":
    asyncio.run(main())
