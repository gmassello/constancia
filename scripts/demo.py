import asyncio
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.calls import Call, register  # noqa: E402
from app.channel import ScriptedPatient  # noqa: E402
from app.llm import GeminiLLM, ScriptedLLM  # noqa: E402
from app.memory import load_seed  # noqa: E402
from app.orchestrator import run_call  # noqa: E402
from app.packs import get_pack  # noqa: E402

PATIENT_ID = "8c9d0e1f-2a3b-4c5d-6e7f-8091a2b3c4d5"

WEEK_1 = [
    "Hola, sí, soy Ana.",
    "La rodilla derecha me duele siete de diez, sobre todo cuando subo escaleras.",
    "Los ejercicios los hice tres veces, me salté dos días porque estuve con mucho trabajo.",
    "Después de los ejercicios me queda un poco rígida, nada raro.",
    "No, caídas no tuve, nada de eso.",
]

WEEK_2 = [
    "Hola, sí, soy Ana.",
    "La rodilla mejoró bastante, ahora me duele cuatro de diez al subir escaleras.",
    "Esta semana los hice cinco veces, me organicé mejor.",
    "No, ninguna molestia nueva.",
    "No, nada de eso.",
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


def scripted_facts(facts: list[dict]) -> str:
    by_term = {fact["term"]: fact["id"] for fact in facts}
    return json.dumps(
        {
            "facts": [
                {
                    "fact": "dolor en la rodilla derecha 4/10 al subir escaleras",
                    "term": "rodilla derecha",
                    "category": "symptom",
                    "value": 4,
                    "quote": "me duele cuatro de diez",
                    "turn_id": 4,
                    "confidence": 0.95,
                    "supersedes": by_term.get("rodilla derecha"),
                },
                {
                    "fact": "hizo los ejercicios cinco veces en la semana",
                    "term": "ejercicios en casa",
                    "category": "adherence",
                    "value": 5,
                    "quote": "los hice cinco veces",
                    "turn_id": 6,
                    "confidence": 0.9,
                    "supersedes": by_term.get("ejercicios en casa"),
                },
            ]
        }
    )


def build_llm(structured: list[str]):
    if not os.environ.get("GEMINI_API_KEY"):
        return ScriptedLLM(structured_replies=structured)
    for key, value in PLACEHOLDERS.items():
        os.environ.setdefault(key, value)
    return GeminiLLM()


async def main() -> None:
    with_memory = os.environ.get("MEMORY", "").lower() in ("on", "1", "true")
    store = load_seed() if with_memory else None
    facts = await store.current_facts(PATIENT_ID) if store else []

    call = register(
        Call(
            patient_id=PATIENT_ID,
            patient_name="Ana",
            pack=get_pack("rehab"),
            memory=with_memory,
        )
    )
    channel = ScriptedPatient(call, list(WEEK_2 if with_memory else WEEK_1))
    llm = build_llm([scripted_facts(facts)] if with_memory else [])
    await run_call(call, channel, llm, store, silence_s=0.1)

    for turn in call.transcript:
        who = "agente " if turn["speaker"] == "agent" else "paciente"
        print(f"{turn['turn_id']:>2} {who}  {turn['text']}")
    print()
    for event in call.trace:
        print(json.dumps(event, ensure_ascii=False))
    print()
    print("keyterms:", json.dumps(channel.keyterms, ensure_ascii=False))
    print("answers:", json.dumps(call.answers, ensure_ascii=False))
    print("escalated:", call.escalated)
    print("summary:", call.summary)


if __name__ == "__main__":
    asyncio.run(main())
