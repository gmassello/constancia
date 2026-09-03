import asyncio
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.calls import Call, register  # noqa: E402
from app.channel import ScriptedPatient  # noqa: E402
from app.llm import GeminiLLM, ScriptedLLM  # noqa: E402
from app.orchestrator import run_call  # noqa: E402
from app.packs import get_pack  # noqa: E402

WEEK_1 = [
    "Hola, sí, soy Ana.",
    "La rodilla derecha me duele siete de diez, sobre todo cuando subo escaleras.",
    "Los ejercicios los hice tres veces, me salté dos días porque estuve con mucho trabajo.",
    "Después de los ejercicios me queda un poco rígida, nada raro.",
    "No, caídas no tuve, nada de eso.",
]

PLACEHOLDERS = {
    "ASSEMBLYAI_API_KEY": "unused-in-demo",
    "ELEVENLABS_API_KEY": "unused-in-demo",
    "ELEVENLABS_VOICE_ID": "unused-in-demo",
    "TWILIO_ACCOUNT_SID": "unused-in-demo",
    "TWILIO_AUTH_TOKEN": "unused-in-demo",
    "TWILIO_NUMBER": "+541100000000",
    "PUBLIC_BASE_URL": "http://localhost:8000",
}


def build_llm():
    if not os.environ.get("GEMINI_API_KEY"):
        return ScriptedLLM()
    for key, value in PLACEHOLDERS.items():
        os.environ.setdefault(key, value)
    return GeminiLLM()


async def main() -> None:
    call = register(Call(patient_id="demo", patient_name="Ana", pack=get_pack("rehab")))
    channel = ScriptedPatient(call, list(WEEK_1))
    await run_call(call, channel, build_llm(), silence_s=0.1)

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
