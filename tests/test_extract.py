import json

from app import extract
from app.calls import Call
from app.extract import Fact
from app.packs import get_pack

TRANSCRIPT = [
    {"turn_id": 1, "speaker": "agent", "text": "¿Cuánto te duele del uno al diez?"},
    {"turn_id": 2, "speaker": "patient", "text": "La rodilla derecha me duele siete de diez."},
]

VALID = {
    "fact": "dolor en la rodilla derecha 7/10",
    "term": "rodilla derecha",
    "category": "symptom",
    "value": 7,
    "quote": "me duele siete de diez",
    "turn_id": 2,
    "confidence": 0.9,
    "supersedes": None,
}


class FakeLLM:
    def __init__(self, replies: list[str]) -> None:
        self.replies = list(replies)
        self.prompts: list[str] = []

    async def structured(self, system: str, user: str, schema) -> str:
        self.prompts.append(user)
        return self.replies.pop(0)


def build(replies: list[str]) -> tuple[Call, FakeLLM]:
    call = Call(patient_id="test", patient_name="Ana", pack=get_pack("rehab"))
    call.transcript = list(TRANSCRIPT)
    return call, FakeLLM(replies)


def types_of(call: Call) -> list[str]:
    return [event["type"] for event in call.trace]


def test_a_quote_from_a_patient_turn_is_grounded() -> None:
    assert extract.ground(Fact(**VALID), TRANSCRIPT)


def test_a_quote_from_an_agent_turn_is_rejected() -> None:
    fact = Fact(**{**VALID, "quote": "Cuánto te duele del uno al diez", "turn_id": 1})
    assert not extract.ground(fact, TRANSCRIPT)


def test_a_quote_that_is_not_in_the_turn_is_rejected() -> None:
    assert not extract.ground(Fact(**{**VALID, "quote": "me caí en el baño"}), TRANSCRIPT)


def test_grounding_ignores_accents_and_case() -> None:
    assert extract.ground(Fact(**{**VALID, "quote": "ME DUELE SIETE DE DIEZ"}), TRANSCRIPT)


async def test_run_keeps_grounded_facts_and_drops_the_rest() -> None:
    invented = {**VALID, "fact": "se cayó", "quote": "me caí en el baño"}
    call, llm = build([json.dumps({"facts": [VALID, invented]})])

    facts = await extract.run(call, llm, [])

    assert [fact.fact for fact in facts] == [VALID["fact"]]
    assert "fact_rejected" in types_of(call)


async def test_run_retries_when_the_reply_does_not_validate() -> None:
    call, llm = build(['{"facts": [{"fact": "sin cita"}]}', json.dumps({"facts": [VALID]})])

    facts = await extract.run(call, llm, [])

    assert len(facts) == 1
    assert "extract_retry" in types_of(call)
    assert "rejected" in llm.prompts[1]


async def test_run_gives_up_after_three_attempts() -> None:
    call, llm = build(['{"facts": [{}]}'] * extract.MAX_ATTEMPTS)

    assert await extract.run(call, llm, []) == []
    assert "extract_failed" in types_of(call)


async def test_supersedes_pointing_at_an_unknown_fact_is_dropped() -> None:
    call, llm = build([json.dumps({"facts": [{**VALID, "supersedes": "not-a-known-id"}]})])

    known = [{"id": "known", "category": "symptom", "fact": "x", "reported_at": "2026-01-01"}]
    facts = await extract.run(call, llm, known)

    assert facts[0].supersedes is None


def test_the_prompt_carries_the_existing_facts_with_their_ids() -> None:
    call = Call(patient_id="test", patient_name="Ana", pack=get_pack("rehab"))
    call.transcript = list(TRANSCRIPT)
    facts = [
        {"id": "abc", "category": "symptom", "fact": "dolor 7/10", "reported_at": "2026-01-01"}
    ]

    text = extract.prompt(call, facts)

    assert "abc" in text and "dolor 7/10" in text
    assert "2 patient: La rodilla derecha me duele siete de diez." in text
