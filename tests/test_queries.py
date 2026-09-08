from app import queries
from app.memory import load_seed
from app.packs import get_pack

PATIENT = "8c9d0e1f-2a3b-4c5d-6e7f-8091a2b3c4d5"
WEEK_1 = "2026-08-31T10:00:00+00:00"
WEEK_2 = "2026-09-07T10:00:00+00:00"


async def rows() -> list[dict]:
    return await load_seed().chain(PATIENT)


def knee(value: float, reported_at: str, fact_id: str) -> dict:
    return {
        "id": fact_id,
        "term": "rodilla derecha",
        "category": "symptom",
        "value": value,
        "reported_at": reported_at,
        "superseded_by": None,
    }


async def test_chain_returns_every_seed_fact_with_no_history() -> None:
    facts = queries.chain(await rows())

    assert [f["term"] for f in facts] == [
        "rodilla derecha",
        "ejercicios en casa",
        "rigidez",
        "caída en el baño",
    ]
    assert all(fact["superseded"] == [] for fact in facts)


async def test_chain_hangs_the_retired_fact_under_the_one_that_replaced_it() -> None:
    store = load_seed()
    old = store.chain_sync(PATIENT)[0]
    store.facts.append({**old, "id": "new-id", "value": 4, "reported_at": WEEK_2})
    await store.supersede(old["id"], "new-id")

    facts = queries.chain(await store.chain(PATIENT))
    replacement = next(f for f in facts if f["id"] == "new-id")

    assert old["id"] not in [f["id"] for f in facts]
    assert [f["value"] for f in replacement["superseded"]] == [7]


async def test_chain_walks_a_supersession_longer_than_one_step() -> None:
    facts = queries.chain(
        [
            {**knee(4, WEEK_2, "c"), "superseded_by": None},
            {**knee(7, WEEK_1, "b"), "superseded_by": "c"},
            {**knee(9, WEEK_1, "a"), "superseded_by": "b"},
        ]
    )

    assert [f["id"] for f in facts] == ["c"]
    assert [f["id"] for f in facts[0]["superseded"]] == ["b", "a"]


async def test_weekly_follows_one_term_and_takes_the_newest_value_per_week() -> None:
    weeks = queries.weekly([knee(7, WEEK_1, "a"), knee(4, WEEK_2, "b")])

    assert [w["week"] for w in weeks] == ["2026-W36", "2026-W37"]
    assert [w["value"] for w in weeks] == [7.0, 4.0]
    assert {w["term"] for w in weeks} == {"rodilla derecha"}


async def test_weekly_is_empty_when_no_fact_carries_a_number() -> None:
    assert queries.weekly([]) == []
    assert queries.weekly([f for f in await rows() if f["value"] is None]) == []


async def test_keyterms_at_ignores_facts_the_call_itself_produced() -> None:
    store = load_seed()
    call = (await store.calls(PATIENT))[0]
    rows = await store.chain(PATIENT)

    assert queries.keyterms_at(rows, call["started_at"], get_pack("rehab")) == []


async def test_keyterms_at_carries_the_previous_week_into_the_next_call() -> None:
    store = load_seed()

    terms = queries.keyterms_at(await store.chain(PATIENT), WEEK_2, get_pack("rehab"))

    assert terms == ["rodilla derecha", "ejercicios en casa", "rigidez", "caída en el baño"]
