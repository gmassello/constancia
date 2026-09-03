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
    assert phases_done(call) == ["greet", "recall", "converse", "extract", "store", "summarize"]
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
