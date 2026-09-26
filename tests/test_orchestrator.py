import pytest

from app import orchestrator
from app.calls import Call
from app.channel import ScriptedPatient
from app.extract import Fact
from app.llm import ScriptedLLM
from app.packs import ASK_MARKER, get_pack

HELLO = "Hello, yes, this is Ana."
WEEK_1 = [
    HELLO,
    "My right knee hurts seven out of ten when I climb stairs.",
    "I did the exercises three times.",
    "It stays a little stiff, nothing strange.",
    "No, nothing like that.",
]


def build(answers: list[str | None]) -> tuple[Call, ScriptedPatient, ScriptedLLM]:
    call = Call(patient_id="test", patient_name="Ana", pack=get_pack("rehab"))
    return call, ScriptedPatient(call, answers), ScriptedLLM()


def types_of(call: Call) -> list[str]:
    return [event["type"] for event in call.trace]


def phases_done(call: Call) -> list[str]:
    return [e["phase"] for e in call.trace if e["type"] == "phase_done"]


async def test_full_protocol_asks_every_question_in_order() -> None:
    call, channel, llm = build(WEEK_1)
    await orchestrator.run_call(call, channel, llm, silence_s=0.01)

    assert list(call.answers) == ["pain", "adherence", "side_effects", "red_flags"]
    assert call.escalated is None
    assert channel.said[-1] == call.pack.goodbye
    assert phases_done(call) == ["recall", "greet", "converse", "extract", "store", "summarize"]
    assert call.summary


async def test_red_flag_ends_the_protocol_early() -> None:
    call, channel, llm = build([HELLO, "Yesterday I fell coming down the stairs."])
    await orchestrator.run_call(call, channel, llm, silence_s=0.01)

    assert call.escalated["rule"] == "fall"
    assert "guard_hit" in types_of(call)
    assert call.answers == {}
    assert call.pack.goodbye not in channel.said


async def test_a_red_flag_in_the_greeting_escalates_before_any_question() -> None:
    call, channel, llm = build(["Not great, I fell coming down the stairs on Tuesday."])
    await orchestrator.run_call(call, channel, llm, silence_s=0.01)

    assert call.escalated["rule"] == "fall"
    assert "guard_hit" in types_of(call)
    assert call.answers == {}
    assert call.pack.goodbye not in channel.said
    assert not any(ASK_MARKER in prompt for prompt in llm.prompts)


async def test_silence_reprompts_once_then_closes() -> None:
    call, channel, llm = build([HELLO, None, None])
    await orchestrator.run_call(call, channel, llm, silence_s=0.01)

    assert call.pack.reprompt in channel.said
    assert channel.said[-1] == call.pack.goodbye_silent
    assert call.answers == {}


async def test_non_critical_phase_fails_soft() -> None:
    async def boom(call, channel, llm, silence_s):
        raise RuntimeError("no database yet")

    call, channel, llm = build(WEEK_1)
    original = orchestrator.PHASES
    orchestrator.PHASES = tuple(
        (name, boom if name == "recall" else fn, critical) for name, fn, critical in original
    )
    try:
        await orchestrator.run_call(call, channel, llm, silence_s=0.01)
    finally:
        orchestrator.PHASES = original

    failed = [e for e in call.trace if e["type"] == "phase_failed"]
    assert [e["phase"] for e in failed] == ["recall"]
    assert failed[0]["critical"] is False
    assert list(call.answers) == ["pain", "adherence", "side_effects", "red_flags"]


async def test_hangup_mid_call_still_reaches_summarize() -> None:
    call, channel, llm = build([HELLO, "It hurts three out of ten."])
    await orchestrator.run_call(call, channel, llm, silence_s=0.01)

    assert "patient_hung_up" in types_of(call)
    assert call.answers == {"pain": "It hurts three out of ten."}
    assert "summarize" in phases_done(call)
    assert call.summary


async def test_the_llm_is_told_which_question_to_ask() -> None:
    call, channel, llm = build(WEEK_1)
    await orchestrator.run_call(call, channel, llm, silence_s=0.01)

    asked = [p for p in llm.prompts if ASK_MARKER in p]
    goals = [q.goal for q in call.pack.questions]
    assert [g for g in goals if any(g in p for p in asked)] == goals


@pytest.mark.parametrize("pack_key", ["rehab", "postpartum", "chronic"])
async def test_every_pack_runs_end_to_end(pack_key: str) -> None:
    call = Call(patient_id="test", patient_name="Ana", pack=get_pack(pack_key))
    channel = ScriptedPatient(call, [HELLO] + ["All good, nothing new."] * 4)
    await orchestrator.run_call(call, channel, ScriptedLLM(), silence_s=0.01)

    assert len(call.answers) == len(call.pack.questions)
    assert call.escalated is None


PATIENT = "8c9d0e1f-2a3b-4c5d-6e7f-8091a2b3c4d5"
WEEK_2 = [
    HELLO,
    "My knee is a lot better, it is four out of ten on the stairs now.",
    "I managed five of the seven days.",
    "I did them five times this week.",
    "No, no new discomfort.",
    "No, nothing like that.",
]
SUPERSEDING = {
    "fact": "right knee pain 4/10 climbing stairs",
    "term": "right knee",
    "category": "symptom",
    "value": 4,
    "quote": "it is four out of ten",
    "turn_id": 5,
    "confidence": 0.9,
}
SUPERSEDING_FACT = Fact(**SUPERSEDING)


def build_week_2(memory: bool) -> tuple[Call, ScriptedPatient, ScriptedLLM, object]:
    import json

    from app.memory import load_seed

    store = load_seed()
    old = store.chain_sync(PATIENT)[0]
    extracted = json.dumps({"facts": [{**SUPERSEDING, "supersedes": old["id"]}]})
    llm = ScriptedLLM(structured_replies=[extracted])
    call = Call(patient_id=PATIENT, patient_name="Ana", pack=get_pack("rehab"), memory=memory)
    return call, ScriptedPatient(call, list(WEEK_2)), llm, store


async def test_memory_on_puts_the_previous_facts_in_the_prompt() -> None:
    call, channel, llm, store = build_week_2(memory=True)
    await orchestrator.run_call(call, channel, llm, store, silence_s=0.01)

    assert "right knee" in llm.prompts[0]
    assert channel.keyterms[0] == "right knee"
    assert [e["type"] for e in call.trace if e["type"] == "fact_superseded"] == ["fact_superseded"]
    current = await store.current_facts(PATIENT)
    assert [f["value"] for f in current if f["term"] == "right knee"] == [4]


async def test_what_assemblyai_heard_is_shown_but_never_primes_the_next_call() -> None:
    # ponytail: the loop was built, measured on a real recording and taken back out. The phrases
    # come off the whole recording, so they carry the agent's own lines, common words the API warns
    # cause overcorrections, and — the reason it went — the patient's name as the recogniser
    # mis-heard it, which priming would then reinforce every week. scripts/keyphrases-measured.json
    # holds the run. Reconnect it the day the phrases are filtered against entities and the pack.
    call, channel, llm, store = build_week_2(memory=True)
    seeded = (await store.calls(PATIENT))[0]
    await store.save_analysis(str(seeded["id"]), {"phrases": [{"text": "the stairs", "count": 2}]})

    await orchestrator.run_call(call, channel, llm, store, silence_s=0.01)

    assert channel.keyterms[0] == "right knee"
    assert "the stairs" not in channel.keyterms
    recall = next(e for e in call.trace if e["type"] == "recall")
    assert "the stairs" not in recall["keyterms"]


async def test_the_greeting_is_told_to_quote_last_week_only_when_there_is_memory() -> None:
    from app.packs import GREET_RECALL

    on, channel, llm, store = build_week_2(memory=True)
    await orchestrator.run_call(on, channel, llm, store, silence_s=0.01)
    greeting = next(p for p in llm.prompts if on.pack.greet in p)
    assert GREET_RECALL in greeting
    assert "right knee pain 7/10 climbing stairs" in greeting

    off, channel, llm, store = build_week_2(memory=False)
    await orchestrator.run_call(off, channel, llm, store, silence_s=0.01)
    greeting = next(p for p in llm.prompts if off.pack.greet in p)
    assert GREET_RECALL not in greeting


async def test_the_summary_reaches_the_stored_call() -> None:
    call, channel, llm, store = build_week_2(memory=True)
    await orchestrator.run_call(call, channel, llm, store, silence_s=0.01)

    saved = await store.call(call.id)
    assert call.summary
    assert saved["summary"] == call.summary


async def test_memory_off_never_mentions_the_knee() -> None:
    call, channel, llm, store = build_week_2(memory=False)
    before = await store.current_facts(PATIENT)
    await orchestrator.run_call(call, channel, llm, store, silence_s=0.01)

    spoken = [p for p in llm.prompts if ASK_MARKER in p or call.pack.greet in p]
    assert spoken and not any("knee" in prompt for prompt in spoken)
    assert channel.keyterms == []
    assert await store.current_facts(PATIENT) == before
    assert "memory_off" in types_of(call)


async def test_memory_off_still_records_that_the_call_happened() -> None:
    call, channel, llm, store = build_week_2(memory=False)
    await orchestrator.run_call(call, channel, llm, store, silence_s=0.01)

    row = await store.call(call.id)
    assert row is not None
    assert row["memory_enabled"] is False
    assert row["summary"] == call.summary
    assert row["transcript"] == call.transcript


async def test_a_critical_phase_failing_still_records_that_the_call_happened() -> None:
    async def boom(call, channel, llm, store, silence_s):
        raise RuntimeError("gemini is down")

    call, channel, llm, store = build_week_2(memory=True)
    original = orchestrator.PHASES
    orchestrator.PHASES = tuple(
        (name, boom if name == "converse" else fn, critical) for name, fn, critical in original
    )
    try:
        await orchestrator.run_call(call, channel, llm, store, silence_s=0.01)
    finally:
        orchestrator.PHASES = original

    assert phases_done(call) == ["recall", "greet"]
    row = await store.call(call.id)
    assert row is not None
    assert row["transcript"] == call.transcript


async def test_a_fact_that_fails_to_store_names_the_ones_that_were_lost() -> None:
    call, channel, llm, store = build_week_2(memory=True)
    call.new_facts = [SUPERSEDING_FACT, SUPERSEDING_FACT, SUPERSEDING_FACT]

    async def refuse(text: str, emit=None):
        raise RuntimeError("gemini embeddings failed after 4 attempts: 429")

    store.embed = refuse
    with pytest.raises(RuntimeError):
        await orchestrator.store_facts(call, channel, llm, store, 0.01)

    lost = [e for e in call.trace if e["type"] == "facts_lost"]
    assert len(lost) == 1
    assert lost[0]["count"] == 3
    assert lost[0]["stored"] == 0


async def test_an_embedding_retry_reaches_the_trace() -> None:
    call, channel, llm, store = build_week_2(memory=True)
    call.new_facts = [SUPERSEDING_FACT]
    seen: list[str] = []

    async def slow(text: str, emit=None):
        if emit:
            emit("llm_retry", code=429, attempt=1, delay_s=5.0)
        seen.append(text)
        return [0.0] * 8

    store.embed = slow
    await orchestrator.store_facts(call, channel, llm, store, 0.01)

    assert seen == [SUPERSEDING_FACT.fact]
    assert "llm_retry" in types_of(call)


async def test_without_a_store_the_memory_phases_are_skipped() -> None:
    call, channel, llm = build(WEEK_1)
    await orchestrator.run_call(call, channel, llm, None, silence_s=0.01)

    reasons = [e["reason"] for e in call.trace if e["type"] == "memory_off"]
    assert reasons == ["no memory store configured"] * 2
    assert list(call.answers) == ["pain", "adherence", "side_effects", "red_flags"]


class DroppingPatient(ScriptedPatient):
    def __init__(self, call: Call, answers: list[str | None], dropped: list[str]) -> None:
        super().__init__(call, answers)
        self.dropped = list(dropped)

    def take_dropped(self) -> list[str]:
        dropped, self.dropped = self.dropped, []
        return dropped


async def test_a_turn_the_channel_dropped_still_goes_through_the_guard() -> None:
    call = Call(patient_id="test", patient_name="Ana", pack=get_pack("rehab"))
    channel = DroppingPatient(call, WEEK_1, ["and I fell on Tuesday coming down the stairs"])
    await orchestrator.run_call(call, channel, ScriptedLLM(), silence_s=0.01)

    assert call.escalated["rule"] == "fall"
    assert "guard_hit" in types_of(call)


async def test_a_hangup_in_the_greeting_skips_the_live_phases_and_still_summarizes() -> None:
    class RateLimitedLLM(ScriptedLLM):
        async def reply(self, system, history, emit=None):
            if ASK_MARKER in system:
                raise RuntimeError("429 after every retry")
            return await super().reply(system, history, emit)

    call = Call(patient_id="test", patient_name="Ana", pack=get_pack("rehab"))
    await orchestrator.run_call(call, ScriptedPatient(call, []), RateLimitedLLM(), silence_s=0.01)

    assert "phase_failed" not in types_of(call)
    assert phases_done(call) == ["recall", "extract", "store", "summarize"]
    assert call.ended_at is not None


PROMISED = {
    "id": "fact-1",
    "fact": "promised to walk every morning",
    "term": "daily walks",
    "category": "commitment",
    "value": None,
    "quote": "I will walk every morning",
    "turn_id": 4,
    "reported_at": "2026-09-15T10:00:00+00:00",
    "valid_until": None,
    "superseded_by": None,
}


def test_with_nothing_promised_the_question_list_is_the_packs_own() -> None:
    call = Call(patient_id="test", patient_name="Ana", pack=get_pack("rehab"))

    assert orchestrator.questions_for(call.pack, call.facts) == list(call.pack.questions)


def test_a_standing_promise_adds_one_question_before_adherence() -> None:
    call = Call(patient_id="test", patient_name="Ana", pack=get_pack("rehab"))
    call.facts = [PROMISED]

    keys = [question.key for question in orchestrator.questions_for(call.pack, call.facts)]

    assert keys == ["pain", "commitment", "adherence", "side_effects", "red_flags"]


async def test_the_promise_question_is_asked_and_its_answer_recorded() -> None:
    call, channel, llm = build([HELLO, *WEEK_1[1:2], "I walked four mornings", *WEEK_1[2:]])
    call.facts = [PROMISED]

    await orchestrator.run_call(call, channel, llm, silence_s=0.01)

    assert list(call.answers) == [
        "pain",
        "commitment",
        "adherence",
        "side_effects",
        "red_flags",
    ]
    assert call.answers["commitment"] == "I walked four mornings"


def test_the_memory_block_keeps_promises_in_their_own_paragraph() -> None:
    from app.packs import MEMORY_HEADER, PROMISE_HEADER, memory_block

    reported = {**PROMISED, "category": "symptom", "fact": "right knee pain 7/10"}

    block = memory_block([reported, PROMISED])

    assert MEMORY_HEADER in block and PROMISE_HEADER in block
    assert block.index(MEMORY_HEADER) < block.index(PROMISE_HEADER)
    assert "right knee pain 7/10" in block.split(PROMISE_HEADER)[0]


def test_with_only_promises_the_reported_header_is_left_out() -> None:
    from app.packs import MEMORY_HEADER, PROMISE_HEADER, memory_block

    block = memory_block([PROMISED])

    assert PROMISE_HEADER in block and MEMORY_HEADER not in block


async def test_clinical_advice_is_replaced_by_the_packs_own_question() -> None:
    call, channel, _ = build(WEEK_1)
    llm = ScriptedLLM(replies=["Hi Ana, how is the week going?", "You should double the dose."])

    await orchestrator.run_call(call, channel, llm, silence_s=0.01)

    pain = next(q for q in call.pack.questions if q.key == "pain")
    assert pain.fallback in channel.said
    assert "double the dose" not in " ".join(channel.said)
    revised = [e for e in call.trace if e["type"] == "critic_revise"]
    assert revised[0]["reason"] == "clinical advice"
    assert revised[0]["said"] == "You should double the dose."


async def test_a_reply_the_critic_passes_is_spoken_as_the_model_wrote_it() -> None:
    call, channel, _ = build(WEEK_1)
    asked = "How much does the knee hurt today, from one to ten?"
    llm = ScriptedLLM(replies=["Hi Ana, how is the week going?", asked])

    await orchestrator.run_call(call, channel, llm, silence_s=0.01)

    assert asked in channel.said
    revised = [e["said"] for e in call.trace if e["type"] == "critic_revise"]
    assert asked not in revised


async def test_the_greeting_and_the_summary_are_not_criticised() -> None:
    call, channel, _ = build(WEEK_1)
    llm = ScriptedLLM(replies=["Hi Ana. Good to see you. Nothing here ends in a question."])

    await orchestrator.run_call(call, channel, llm, silence_s=0.01)

    assert channel.said[0] == "Hi Ana. Good to see you. Nothing here ends in a question."


MUMBLED = {"text": "My right knee hurts seven out of ten.", "low_conf": ["seven"]}


async def test_a_number_heard_badly_is_read_back_once() -> None:
    call, channel, llm = build([HELLO, MUMBLED, "Yes, seven.", *WEEK_1[2:]])

    await orchestrator.run_call(call, channel, llm, silence_s=0.01)

    from app.packs import CONFIRM

    read_back = CONFIRM.format(value="seven")
    assert channel.said.count(read_back) == 1
    assert [e["words"] for e in call.trace if e["type"] == "low_confidence"] == [["seven"]]


async def test_a_number_heard_clearly_is_never_read_back() -> None:
    call, channel, llm = build(WEEK_1)

    await orchestrator.run_call(call, channel, llm, silence_s=0.01)

    assert [e for e in call.trace if e["type"] == "low_confidence"] == []
    assert list(call.answers) == ["pain", "adherence", "side_effects", "red_flags"]


async def test_a_red_flag_in_the_read_back_still_escalates() -> None:
    call, channel, llm = build([HELLO, MUMBLED, "Yes, and I fell on Tuesday."])

    await orchestrator.run_call(call, channel, llm, silence_s=0.01)

    assert call.escalated is not None
    assert call.escalated["rule"] == "fall"


async def test_an_answered_question_is_spoken_word_for_word_and_then_retired() -> None:
    from app.memory import load_seed
    from app.packs import ANSWER_RELAY

    store = load_seed()
    answered = next(r for r in store.questions_rows if r["status"] == "answered")
    call = Call(patient_id=PATIENT, patient_name="Ana", pack=get_pack("rehab"), memory=True)
    channel = ScriptedPatient(call, list(WEEK_2))

    await orchestrator.run_call(call, channel, ScriptedLLM(), store, silence_s=0.01)

    assert ANSWER_RELAY.format(answer=answered["answer"]) in channel.said
    assert next(r for r in store.questions_rows if r["id"] == answered["id"])["status"] == (
        "delivered"
    )
    assert [e["answer"] for e in call.trace if e["type"] == "answer_delivered"] == [
        answered["answer"]
    ]


async def test_an_answer_is_read_out_only_once() -> None:
    from app.memory import load_seed
    from app.packs import ANSWER_RELAY

    store = load_seed()
    answered = next(r for r in store.questions_rows if r["status"] == "answered")
    relay = ANSWER_RELAY.format(answer=answered["answer"])

    for _ in range(2):
        call = Call(patient_id=PATIENT, patient_name="Ana", pack=get_pack("rehab"), memory=True)
        channel = ScriptedPatient(call, list(WEEK_2))
        await orchestrator.run_call(call, channel, ScriptedLLM(), store, silence_s=0.01)
        said = channel.said

    assert relay not in said


async def test_with_memory_off_no_answer_is_read_out() -> None:
    from app.memory import load_seed

    store = load_seed()
    call = Call(patient_id=PATIENT, patient_name="Ana", pack=get_pack("rehab"), memory=False)
    channel = ScriptedPatient(call, list(WEEK_2))

    await orchestrator.run_call(call, channel, ScriptedLLM(), store, silence_s=0.01)

    assert [e for e in call.trace if e["type"] == "answer_delivered"] == []


async def test_asking_for_a_person_flags_the_call_without_ending_it() -> None:
    call, channel, llm = build([HELLO, "I want to talk to my doctor", *WEEK_1[2:]])

    await orchestrator.run_call(call, channel, llm, silence_s=0.01)

    assert call.wants_human is True
    assert call.escalated is None
    assert phases_done(call) == ["recall", "greet", "converse", "extract", "store", "summarize"]
    assert [e["quote"] for e in call.trace if e["type"] == "wants_human"] == [
        "I want to talk to my doctor"
    ]
    assert call.trace[-1]["wants_human"] is True


async def test_the_handoff_flag_is_raised_once_however_often_it_is_asked() -> None:
    call, channel, llm = build(
        [HELLO, "I want to talk to my doctor", "I need a human", *WEEK_1[3:]]
    )

    await orchestrator.run_call(call, channel, llm, silence_s=0.01)

    assert len([e for e in call.trace if e["type"] == "wants_human"]) == 1


async def test_an_extracted_question_is_written_to_the_queue() -> None:
    import json

    from app.memory import load_seed

    store = load_seed()
    call = Call(patient_id=PATIENT, patient_name="Ana", pack=get_pack("rehab"), memory=True)
    channel = ScriptedPatient(call, list(WEEK_2))
    asked = {
        "question": "Can she go back to the stairs?",
        "quote": "I managed five of the seven days",
        "turn_id": 7,
    }
    llm = ScriptedLLM(structured_replies=[json.dumps({"facts": [], "open_questions": [asked]})])

    await orchestrator.run_call(call, channel, llm, store, silence_s=0.01)

    stored = [e for e in call.trace if e["type"] == "question_stored"]
    assert [e["question"] for e in stored] == ["Can she go back to the stairs?"]
    assert any(r["question"] == "Can she go back to the stairs?" for r in store.questions_rows)
