import json

from app import extract
from app.calls import Call
from app.extract import Fact
from app.packs import get_pack

TRANSCRIPT = [
    {"turn_id": 1, "speaker": "agent", "text": "How much does it hurt from one to ten?"},
    {"turn_id": 2, "speaker": "patient", "text": "My right knee hurts seven out of ten."},
]

VALID = {
    "fact": "right knee pain 7/10",
    "term": "right knee",
    "category": "symptom",
    "value": 7,
    "quote": "hurts seven out of ten",
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
    fact = Fact(**{**VALID, "quote": "How much does it hurt from one to ten", "turn_id": 1})
    assert not extract.ground(fact, TRANSCRIPT)


def test_a_quote_that_is_not_in_the_turn_is_rejected() -> None:
    assert not extract.ground(Fact(**{**VALID, "quote": "I fell in the bathroom"}), TRANSCRIPT)


def test_grounding_ignores_accents_and_case() -> None:
    assert extract.ground(Fact(**{**VALID, "quote": "HURTS SEVEN OUT OF TEN"}), TRANSCRIPT)


async def test_run_keeps_grounded_facts_and_drops_the_rest() -> None:
    invented = {**VALID, "fact": "fell over", "quote": "I fell in the bathroom"}
    call, llm = build([json.dumps({"facts": [VALID, invented]})])

    facts, _ = await extract.run(call, llm, [])

    assert [fact.fact for fact in facts] == [VALID["fact"]]
    assert "fact_rejected" in types_of(call)


async def test_a_blank_quote_is_rejected_without_losing_the_other_facts() -> None:
    blank = {**VALID, "fact": "fell over", "quote": " "}
    call, llm = build([json.dumps({"facts": [VALID, blank]})])

    facts, _ = await extract.run(call, llm, [])

    assert [fact.fact for fact in facts] == [VALID["fact"]]
    assert "fact_rejected" in types_of(call)
    assert "extract_retry" not in types_of(call)


async def test_run_retries_when_the_reply_does_not_validate() -> None:
    invalid = json.dumps({"facts": [{k: v for k, v in VALID.items() if k != "quote"}]})
    call, llm = build([invalid, json.dumps({"facts": [VALID]})])

    facts, _ = await extract.run(call, llm, [])

    assert len(facts) == 1
    assert "extract_retry" in types_of(call)
    assert "rejected" in llm.prompts[1]


async def test_an_invented_category_is_rejected_and_the_model_gets_a_second_go() -> None:
    invented = json.dumps({"facts": [{**VALID, "category": "pain_level"}]})
    call, llm = build([invented, json.dumps({"facts": [VALID]})])

    facts, _ = await extract.run(call, llm, [])

    assert [fact.category for fact in facts] == ["symptom"]
    assert "extract_retry" in types_of(call)
    assert "pain_level" in llm.prompts[1]


async def test_run_gives_up_after_three_attempts() -> None:
    call, llm = build(['{"facts": [{}]}'] * extract.MAX_ATTEMPTS)

    assert await extract.run(call, llm, []) == ([], [])
    assert "extract_failed" in types_of(call)


async def test_supersedes_pointing_at_an_unknown_fact_is_dropped() -> None:
    call, llm = build([json.dumps({"facts": [{**VALID, "supersedes": "not-a-known-id"}]})])

    known = [{"id": "known", "category": "symptom", "fact": "x", "reported_at": "2026-01-01"}]
    facts, _ = await extract.run(call, llm, known)

    assert facts[0].supersedes is None


def test_the_prompt_carries_the_existing_facts_with_their_ids() -> None:
    call = Call(patient_id="test", patient_name="Ana", pack=get_pack("rehab"))
    call.transcript = list(TRANSCRIPT)
    facts = [
        {"id": "abc", "category": "symptom", "fact": "pain 7/10", "reported_at": "2026-01-01"}
    ]

    text = extract.prompt(call, facts)

    assert "abc" in text and "pain 7/10" in text
    assert "2 patient: My right knee hurts seven out of ten." in text


def test_a_value_above_the_packs_scale_is_out_of_range() -> None:
    fact = Fact(**{**VALID, "value": 14})
    assert not extract.in_range(fact, get_pack("rehab"))


def test_a_negative_value_is_out_of_range() -> None:
    fact = Fact(**{**VALID, "value": -1})
    assert not extract.in_range(fact, get_pack("rehab"))


def test_a_value_inside_the_packs_scale_is_in_range() -> None:
    assert extract.in_range(Fact(**VALID), get_pack("rehab"))


def test_a_fact_with_no_value_is_in_range() -> None:
    fact = Fact(**{**VALID, "category": "red_flag", "value": None})
    assert extract.in_range(fact, get_pack("rehab"))


def test_a_measure_the_pack_leaves_unbounded_takes_any_reading() -> None:
    fact = Fact(**{**VALID, "category": "clinical_value", "value": 140})
    assert extract.in_range(fact, get_pack("chronic"))


def test_a_category_the_pack_does_not_measure_is_not_capped() -> None:
    fact = Fact(**{**VALID, "category": "mood", "value": 99})
    assert extract.in_range(fact, get_pack("rehab"))


async def test_run_drops_an_out_of_range_value_and_keeps_the_rest() -> None:
    impossible = {**VALID, "fact": "right knee pain 14/10", "value": 14}
    call, llm = build([json.dumps({"facts": [VALID, impossible]})])

    facts, _ = await extract.run(call, llm, [])

    assert [fact.value for fact in facts] == [7]
    rejected = [e for e in call.trace if e["type"] == "fact_rejected"]
    assert [e["reason"] for e in rejected] == ["out_of_range"]


PROMISE_TURN = [
    *TRANSCRIPT,
    {"turn_id": 3, "speaker": "agent", "text": "And what are you planning for this week?"},
    {"turn_id": 4, "speaker": "patient", "text": "I will do the exercises every day this week."},
]
PROMISE = {
    "fact": "promised to do the exercises every day",
    "term": "home exercises",
    "category": "commitment",
    "value": None,
    "quote": "I will do the exercises every day",
    "turn_id": 4,
    "confidence": 0.9,
    "supersedes": None,
}


def promising(replies: list[str]) -> tuple[Call, FakeLLM]:
    call, llm = build(replies)
    call.transcript = list(PROMISE_TURN)
    return call, llm


async def test_a_grounded_promise_is_kept_as_a_commitment() -> None:
    call, llm = promising([json.dumps({"facts": [PROMISE]})])

    facts, _ = await extract.run(call, llm, [])

    assert [fact.category for fact in facts] == ["commitment"]


async def test_the_deterministic_score_caps_the_models_confidence() -> None:
    hedged = {
        **PROMISE,
        "quote": "I will do the exercises every day",
        "confidence": 1.0,
    }
    call, llm = promising([json.dumps({"facts": [hedged]})])

    facts, _ = await extract.run(call, llm, [])

    assert facts[0].confidence == 0.9


async def test_a_quoted_request_is_not_a_commitment() -> None:
    asking = [
        *TRANSCRIPT,
        {"turn_id": 3, "speaker": "agent", "text": "Anything else?"},
        {"turn_id": 4, "speaker": "patient", "text": "Can you send me the video?"},
    ]
    call, llm = build([json.dumps({"facts": [{**PROMISE, "quote": "Can you send me the video"}]})])
    call.transcript = asking

    facts, _ = await extract.run(call, llm, [])

    assert facts == []
    rejected = [e for e in call.trace if e["type"] == "fact_rejected"]
    assert [e["reason"] for e in rejected] == ["not a commitment"]


async def test_a_fact_from_a_badly_heard_turn_is_marked_doubtful() -> None:
    call, llm = build([json.dumps({"facts": [VALID]})])
    call.transcript = [
        TRANSCRIPT[0],
        {**TRANSCRIPT[1], "low_conf": ["seven"]},
    ]

    facts, _ = await extract.run(call, llm, [])

    assert facts[0].confidence == extract.DOUBTED


async def test_a_fact_from_a_clean_turn_keeps_the_models_confidence() -> None:
    call, llm = build([json.dumps({"facts": [VALID]})])

    facts, _ = await extract.run(call, llm, [])

    assert facts[0].confidence == 0.9


ASKING = [
    *TRANSCRIPT,
    {"turn_id": 3, "speaker": "agent", "text": "Anything else?"},
    {"turn_id": 4, "speaker": "patient", "text": "Is it normal that my knee clicks?"},
]
QUESTION = {
    "question": "Is a clicking knee normal?",
    "quote": "Is it normal that my knee clicks",
    "turn_id": 4,
}


async def test_a_question_the_agent_deflected_comes_back_as_an_open_question() -> None:
    call, llm = build([json.dumps({"facts": [], "open_questions": [QUESTION]})])
    call.transcript = list(ASKING)

    _, asked = await extract.run(call, llm, [])

    assert [q.question for q in asked] == ["Is a clicking knee normal?"]
    assert [e["count"] for e in call.trace if e["type"] == "questions_found"] == [1]


async def test_a_question_no_patient_turn_backs_is_dropped() -> None:
    invented = {**QUESTION, "quote": "what about swimming"}
    call, llm = build([json.dumps({"facts": [], "open_questions": [invented]})])
    call.transcript = list(ASKING)

    _, asked = await extract.run(call, llm, [])

    assert asked == []
    assert [e["type"] for e in call.trace if e["type"] == "question_rejected"] == [
        "question_rejected"
    ]


async def test_a_reply_with_no_open_questions_key_still_validates() -> None:
    call, llm = build([json.dumps({"facts": [VALID]})])

    facts, asked = await extract.run(call, llm, [])

    assert len(facts) == 1 and asked == []


OTHER_PACK_TURN = [
    *TRANSCRIPT,
    {"turn_id": 3, "speaker": "agent", "text": "And what are you planning for this week?"},
    {"turn_id": 4, "speaker": "patient", "text": "I will log my blood pressure every morning."},
]
OTHER_PACK_PROMISE = {
    **PROMISE,
    "fact": "promised to log blood pressure every morning",
    "term": "blood pressure log",
    "quote": "I will log my blood pressure every morning",
}


def outside_the_vocabulary(replies: list[str]) -> tuple[Call, FakeLLM]:
    call, llm = build(replies)
    call.transcript = list(OTHER_PACK_TURN)
    return call, llm


async def test_a_promise_outside_the_vocabulary_is_dropped_on_its_own() -> None:
    call, llm = outside_the_vocabulary([json.dumps({"facts": [OTHER_PACK_PROMISE]})])

    facts, _ = await extract.run(call, llm, [])

    assert facts == []
    assert "commitment_recalled" not in types_of(call)


async def test_a_second_opinion_rescues_it_and_says_so(monkeypatch) -> None:
    async def commits(quote: str, emit=None) -> float:
        return 0.96

    monkeypatch.setattr("app.commitments.jev.commits", commits)
    call, llm = outside_the_vocabulary([json.dumps({"facts": [OTHER_PACK_PROMISE]})])

    facts, _ = await extract.run(call, llm, [])

    assert [fact.category for fact in facts] == ["commitment"]
    assert facts[0].confidence == 0.75
    assert "commitment_recalled" in types_of(call)
    assert "fact_rejected" not in types_of(call)


async def test_the_vocabulary_answering_first_never_asks_for_a_second_opinion(monkeypatch) -> None:
    async def commits(quote: str, emit=None) -> float:
        raise AssertionError("asked for a second opinion the vocabulary did not need")

    monkeypatch.setattr("app.commitments.jev.commits", commits)
    call, llm = promising([json.dumps({"facts": [PROMISE]})])

    facts, _ = await extract.run(call, llm, [])

    assert [fact.category for fact in facts] == ["commitment"]
    assert "commitment_recalled" not in types_of(call)
