import pytest

from app import orchestrator
from app.calls import Call
from app.channel import ScriptedPatient
from app.llm import ScriptedLLM
from app.packs import get_pack

HELLO = "Hola, sí, soy Ana."
WEEK_1 = [
    HELLO,
    "La rodilla derecha me duele siete de diez cuando subo escaleras.",
    "Los ejercicios los hice tres veces.",
    "Me queda un poco rígida, nada raro.",
    "No, nada de eso.",
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
    call, channel, llm = build([HELLO, "Ayer me caí bajando la escalera."])
    await orchestrator.run_call(call, channel, llm, silence_s=0.01)

    assert call.escalated["rule"] == "fall"
    assert "guard_hit" in types_of(call)
    assert call.answers == {}
    assert call.pack.goodbye not in channel.said


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
    call, channel, llm = build([HELLO, "Me duele tres de diez."])
    await orchestrator.run_call(call, channel, llm, silence_s=0.01)

    assert "patient_hung_up" in types_of(call)
    assert call.answers == {"pain": "Me duele tres de diez."}
    assert "summarize" in phases_done(call)
    assert call.summary


async def test_the_llm_is_told_which_question_to_ask() -> None:
    call, channel, llm = build(WEEK_1)
    await orchestrator.run_call(call, channel, llm, silence_s=0.01)

    asked = [p for p in llm.prompts if "Preguntá sobre:" in p]
    goals = [q.goal for q in call.pack.questions]
    assert [g for g in goals if any(g in p for p in asked)] == goals


@pytest.mark.parametrize("pack_key", ["rehab", "postpartum", "chronic"])
async def test_every_pack_runs_end_to_end(pack_key: str) -> None:
    call = Call(patient_id="test", patient_name="Ana", pack=get_pack(pack_key))
    channel = ScriptedPatient(call, [HELLO] + ["Todo bien, sin novedades."] * 4)
    await orchestrator.run_call(call, channel, ScriptedLLM(), silence_s=0.01)

    assert len(call.answers) == len(call.pack.questions)
    assert call.escalated is None


PATIENT = "8c9d0e1f-2a3b-4c5d-6e7f-8091a2b3c4d5"
WEEK_2 = [
    HELLO,
    "La rodilla mejoró bastante, ahora me duele cuatro de diez al subir escaleras.",
    "Esta semana los hice cinco veces.",
    "No, ninguna molestia nueva.",
    "No, nada de eso.",
]
SUPERSEDING = {
    "fact": "dolor en la rodilla derecha 4/10 al subir escaleras",
    "term": "rodilla derecha",
    "category": "symptom",
    "value": 4,
    "quote": "me duele cuatro de diez",
    "turn_id": 4,
    "confidence": 0.9,
}


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

    assert "rodilla derecha" in llm.prompts[0]
    assert channel.keyterms[0] == "rodilla derecha"
    assert [e["type"] for e in call.trace if e["type"] == "fact_superseded"] == ["fact_superseded"]
    current = await store.current_facts(PATIENT)
    assert [f["value"] for f in current if f["term"] == "rodilla derecha"] == [4]


async def test_memory_off_never_mentions_the_knee() -> None:
    call, channel, llm, store = build_week_2(memory=False)
    await orchestrator.run_call(call, channel, llm, store, silence_s=0.01)

    spoken = [p for p in llm.prompts if "Preguntá sobre:" in p or call.pack.greet in p]
    assert spoken and not any("rodilla" in prompt for prompt in spoken)
    assert channel.keyterms == []
    assert store.saved_calls == []
    assert "memory_off" in types_of(call)


async def test_without_a_store_the_memory_phases_are_skipped() -> None:
    call, channel, llm = build(WEEK_1)
    await orchestrator.run_call(call, channel, llm, None, silence_s=0.01)

    reasons = [e["reason"] for e in call.trace if e["type"] == "memory_off"]
    assert reasons == ["no memory store configured"] * 2
    assert list(call.answers) == ["pain", "adherence", "side_effects", "red_flags"]
