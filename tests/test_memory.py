from app.extract import Fact
from app.memory import FakeStore, keyterms, load_seed, normalize
from app.packs import get_pack

PATIENT = "8c9d0e1f-2a3b-4c5d-6e7f-8091a2b3c4d5"


class Stub:
    id = "call-2"
    patient_id = PATIENT
    started_at = "2026-09-10T00:00:00+00:00"


NEW = Fact(
    fact="dolor en la rodilla derecha 4/10",
    term="rodilla derecha",
    category="symptom",
    value=4,
    quote="cuatro de diez",
    turn_id=4,
)


async def test_the_seed_loads_anas_week_one_facts() -> None:
    facts = await load_seed().current_facts(PATIENT)

    assert [fact["term"] for fact in facts] == [
        "rodilla derecha",
        "ejercicios en casa",
        "rigidez",
        "caída en el baño",
    ]
    assert facts[0]["value"] == 7


async def test_supersede_retires_the_old_fact_but_keeps_it_in_the_chain() -> None:
    store = load_seed()
    old = (await store.current_facts(PATIENT))[0]

    new_id = await store.insert_fact(Stub(), NEW, await store.embed(NEW.fact))
    await store.supersede(old["id"], new_id)

    current = await store.current_facts(PATIENT)
    assert old["id"] not in [fact["id"] for fact in current]
    assert [fact["value"] for fact in current if fact["term"] == "rodilla derecha"] == [4]
    assert old["id"] in [fact["id"] for fact in await store.chain(PATIENT)]


async def test_supersede_does_not_retire_a_fact_twice() -> None:
    store = load_seed()
    old = (await store.current_facts(PATIENT))[0]

    await store.supersede(old["id"], "first")
    await store.supersede(old["id"], "second")

    retired = next(f for f in await store.chain(PATIENT) if f["id"] == old["id"])
    assert retired["superseded_by"] == "first"


async def test_keyterms_only_uses_the_categories_the_pack_asks_for() -> None:
    facts = await load_seed().current_facts(PATIENT)

    assert keyterms(facts, get_pack("rehab")) == [
        "rodilla derecha",
        "ejercicios en casa",
        "rigidez",
        "caída en el baño",
    ]
    without_adherence = ["rodilla derecha", "rigidez", "caída en el baño"]
    assert keyterms(facts, get_pack("postpartum")) == without_adherence


def test_keyterms_deduplicates_and_skips_blanks() -> None:
    facts = [
        {"term": "rodilla derecha", "category": "symptom"},
        {"term": "rodilla derecha", "category": "symptom"},
        {"term": "  ", "category": "symptom"},
        {"term": "sangrado", "category": "mood"},
    ]

    assert keyterms(facts, get_pack("rehab")) == ["rodilla derecha"]


async def test_an_empty_store_has_no_facts_and_no_keyterms() -> None:
    store = FakeStore()

    assert await store.current_facts(PATIENT) == []
    assert keyterms([], get_pack("rehab")) == []


def test_embeddings_are_l2_normalized() -> None:
    vector = normalize([3.0, 4.0])

    assert vector == [0.6, 0.8]
    assert normalize([0.0, 0.0]) == [0.0, 0.0]
