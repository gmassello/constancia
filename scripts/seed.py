import asyncio
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app import db  # noqa: E402
from app.calls import Call  # noqa: E402
from app.extract import Fact  # noqa: E402
from app.memory import SEED_PATH, MemoryStore, days_ago  # noqa: E402
from app.packs import get_pack  # noqa: E402


async def wipe(patient_id: str) -> None:
    await db.execute(
        "delete from patient_memories where patient_id = %s", (patient_id,)
    )
    await db.execute("delete from calls where patient_id = %s", (patient_id,))
    await db.execute("delete from patients where id = %s", (patient_id,))


async def seed_patient(store: MemoryStore, professional_id: str, patient: dict) -> int:
    await wipe(patient["id"])
    await db.execute(
        "insert into patients (id, professional_id, program_type, name, phone_e164, started_at) "
        "values (%s, %s, %s, %s, %s, %s)",
        (
            patient["id"],
            professional_id,
            patient["program_type"],
            patient["name"],
            patient["phone_e164"],
            days_ago(patient["started_age_days"]),
        ),
    )

    stored = 0
    for entry in patient["calls"]:
        call = Call(
            patient_id=patient["id"],
            patient_name=patient["name"],
            pack=get_pack(patient["program_type"]),
            memory=entry["memory_enabled"],
            id=entry["id"],
            started_at=days_ago(entry["age_days"]),
        )
        call.ended_at = call.started_at
        call.transcript = entry["transcript"]
        call.summary = entry["summary"]
        await store.save_call(call)
        for raw in entry["facts"]:
            fact = Fact(**raw)
            await store.insert_fact(call, fact, await store.embed(fact.fact))
            stored += 1
    return stored


async def main() -> None:
    data = json.loads(SEED_PATH.read_text(encoding="utf-8"))
    store = MemoryStore()
    for patient in data["patients"]:
        stored = await seed_patient(store, data["professional_id"], patient)
        print(f"{patient['name']}: {stored} facts")
    await db.close_pool()


if __name__ == "__main__":
    asyncio.run(main())
