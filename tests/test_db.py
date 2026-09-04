import os
import uuid

import pytest

from app import db
from app.calls import Call
from app.extract import Fact
from app.memory import MemoryStore
from app.packs import get_pack

pytestmark = [
    pytest.mark.integration,
    pytest.mark.skipif(not os.environ.get("DATABASE_URL"), reason="needs a live DATABASE_URL"),
]

PROFESSIONAL = "3f1b0e4a-7c2d-4a51-9f8e-1d2c3b4a5e60"


def fact(text: str, value: float) -> Fact:
    return Fact(
        fact=text,
        term="rodilla derecha",
        category="symptom",
        value=value,
        quote=text,
        turn_id=2,
        confidence=0.9,
    )


async def test_a_fact_survives_a_round_trip_and_is_retired_by_supersession() -> None:
    db.init_schema()
    store = MemoryStore()
    patient_id = str(uuid.uuid4())
    call = Call(patient_id=patient_id, patient_name="Ana", pack=get_pack("rehab"))
    embedding = [0.0] * 1535 + [1.0]

    await db.execute(
        "insert into patients (id, professional_id, program_type, name, phone_e164) "
        "values (%s, %s, 'rehab', 'Ana', '+541100000000')",
        (patient_id, PROFESSIONAL),
    )
    try:
        await store.save_call(call)
        old_id = await store.insert_fact(call, fact("dolor 7/10", 7), embedding)

        current = await store.current_facts(patient_id)
        assert [row["fact"] for row in current] == ["dolor 7/10"]
        assert float(current[0]["value"]) == 7.0

        new_id = await store.insert_fact(call, fact("dolor 4/10", 4), embedding)
        await store.supersede(old_id, new_id)

        assert [row["fact"] for row in await store.current_facts(patient_id)] == ["dolor 4/10"]
        retired = next(r for r in await store.chain(patient_id) if str(r["id"]) == old_id)
        assert str(retired["superseded_by"]) == new_id
        assert retired["valid_until"] is not None
    finally:
        await db.execute("delete from patient_memories where patient_id = %s", (patient_id,))
        await db.execute("delete from calls where patient_id = %s", (patient_id,))
        await db.execute("delete from patients where id = %s", (patient_id,))
        await db.close_pool()
