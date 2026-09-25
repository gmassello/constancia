from app.extract import Fact
from app.memory import MAX_KEYTERMS, FakeStore, keyterms, load_seed, normalize, with_phrases
from app.packs import get_pack

PATIENT = "8c9d0e1f-2a3b-4c5d-6e7f-8091a2b3c4d5"


class Stub:
    id = "call-2"
    patient_id = PATIENT
    started_at = "2026-09-10T00:00:00+00:00"


NEW = Fact(
    fact="right knee pain 4/10",
    term="right knee",
    category="symptom",
    value=4,
    quote="four out of ten",
    turn_id=4,
)


async def test_the_seed_loads_anas_week_one_facts() -> None:
    facts = await load_seed().current_facts(PATIENT)

    assert [fact["term"] for fact in facts] == [
        "right knee",
        "home exercises",
        "daily exercises",
        "stiffness",
        "bathroom fall",
    ]
    assert facts[0]["value"] == 7


async def test_supersede_retires_the_old_fact_but_keeps_it_in_the_chain() -> None:
    store = load_seed()
    old = (await store.current_facts(PATIENT))[0]

    new_id = await store.insert_fact(Stub(), NEW, await store.embed(NEW.fact))
    await store.supersede(old["id"], new_id)

    current = await store.current_facts(PATIENT)
    assert old["id"] not in [fact["id"] for fact in current]
    assert [fact["value"] for fact in current if fact["term"] == "right knee"] == [4]
    assert old["id"] in [fact["id"] for fact in await store.chain(PATIENT)]


async def test_inserting_a_superseding_fact_retires_the_old_one_in_one_call() -> None:
    store = load_seed()
    old = (await store.current_facts(PATIENT))[0]

    await store.insert_fact(Stub(), NEW, await store.embed(NEW.fact), old["id"])

    current = await store.current_facts(PATIENT)
    assert old["id"] not in [fact["id"] for fact in current]
    assert [fact["value"] for fact in current if fact["term"] == "right knee"] == [4]
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
        "right knee",
        "home exercises",
        "daily exercises",
        "stiffness",
        "bathroom fall",
    ]
    without_adherence = ["right knee", "stiffness", "bathroom fall"]
    assert keyterms(facts, get_pack("postpartum")) == without_adherence


def test_keyterms_deduplicates_and_skips_blanks() -> None:
    facts = [
        {"term": "right knee", "category": "symptom"},
        {"term": "right knee", "category": "symptom"},
        {"term": "  ", "category": "symptom"},
        {"term": "bleeding", "category": "mood"},
    ]

    assert keyterms(facts, get_pack("rehab")) == ["right knee"]


def test_the_key_phrases_of_the_newest_analysed_call_join_the_vocabulary() -> None:
    calls = [
        {"id": "newest", "analysis": None},
        {"id": "middle", "analysis": {"phrases": [{"text": "the stairs"}, {"text": "Right Knee"}]}},
        {"id": "oldest", "analysis": {"phrases": [{"text": "the pool"}]}},
    ]

    merged = with_phrases(["right knee", "home exercises"], calls)

    assert merged == ["right knee", "home exercises", "the stairs"]


def test_with_no_analysis_on_file_the_vocabulary_is_unchanged() -> None:
    assert with_phrases(["right knee"], [{"id": "c", "analysis": None}]) == ["right knee"]
    assert with_phrases(["right knee"], []) == ["right knee"]


def test_the_merged_vocabulary_respects_the_cap() -> None:
    terms = [f"term {n}" for n in range(MAX_KEYTERMS)]
    calls = [{"id": "c", "analysis": {"phrases": [{"text": "one more"}]}}]

    assert with_phrases(terms, calls) == terms


async def test_an_empty_store_has_no_facts_and_no_keyterms() -> None:
    store = FakeStore()

    assert await store.current_facts(PATIENT) == []
    assert keyterms([], get_pack("rehab")) == []


def test_embeddings_are_l2_normalized() -> None:
    vector = normalize([3.0, 4.0])

    assert vector == [0.6, 0.8]
    assert normalize([0.0, 0.0]) == [0.0, 0.0]


class Asked:
    def __init__(self, question: str, quote: str, turn_id: int) -> None:
        self.question, self.quote, self.turn_id = question, quote, turn_id


async def test_the_seed_loads_anas_questions_newest_first() -> None:
    rows = await load_seed().questions(PATIENT)

    assert [row["status"] for row in rows] == ["answered", "open"]
    assert rows[0]["answer"].startswith("A click with no pain")
    assert rows[1]["answer"] is None


async def test_a_question_is_written_against_the_call_that_asked_it() -> None:
    from app.calls import Call
    from app.packs import get_pack

    store = load_seed()
    call = Call(patient_id=PATIENT, patient_name="Ana", pack=get_pack("rehab"))

    question_id = await store.insert_question(call, Asked("Can she swim?", "can I swim", 6))

    row = next(r for r in await store.questions(PATIENT) if r["id"] == question_id)
    assert row["status"] == "open"
    assert (row["call_id"], row["turn_id"]) == (call.id, 6)


async def test_answering_an_open_question_moves_it_and_keeps_the_answer() -> None:
    store = load_seed()
    open_row = next(r for r in await store.questions(PATIENT) if r["status"] == "open")

    assert await store.set_question(open_row["id"], "open", "answered", "Ice is fine.")

    row = next(r for r in await store.questions(PATIENT) if r["id"] == open_row["id"])
    assert (row["status"], row["answer"]) == ("answered", "Ice is fine.")
    assert row["answered_at"] is not None


async def test_answering_the_same_question_twice_moves_nothing() -> None:
    store = load_seed()
    open_row = next(r for r in await store.questions(PATIENT) if r["status"] == "open")
    await store.set_question(open_row["id"], "open", "answered", "Ice is fine.")

    assert not await store.set_question(open_row["id"], "open", "answered", "Actually no.")

    row = next(r for r in await store.questions(PATIENT) if r["id"] == open_row["id"])
    assert row["answer"] == "Ice is fine."


async def test_delivering_keeps_the_answer_it_was_given() -> None:
    store = load_seed()
    answered = next(r for r in await store.questions(PATIENT) if r["status"] == "answered")

    assert await store.set_question(answered["id"], "answered", "delivered")

    row = next(r for r in await store.questions(PATIENT) if r["id"] == answered["id"])
    assert row["status"] == "delivered"
    assert row["answer"].startswith("A click with no pain")


async def test_a_question_that_is_not_there_moves_nothing() -> None:
    assert not await load_seed().set_question("nope", "open", "answered", "x")
