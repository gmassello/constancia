from app import guard
from app.calls import Call
from app.channel import CallEnded
from app.packs import system_prompt

SILENCE_S = 8.0


async def phrase(call: Call, llm, fragment: str) -> str:
    system = system_prompt(call.pack, call.patient_name, fragment)
    return await llm.reply(system, call.history(), call.emit)


async def ask(call: Call, channel, llm, text: str, silence_s: float) -> str | None:
    await channel.say(text)
    answer = await channel.listen(silence_s)
    if answer is None:
        await channel.say(call.pack.reprompt)
        answer = await channel.listen(silence_s)
    return answer


async def greet(call: Call, channel, llm, silence_s: float) -> None:
    await channel.say(await phrase(call, llm, call.pack.greet))
    await channel.listen(silence_s)


async def recall(call: Call, channel, llm, silence_s: float) -> None:
    call.emit("phase_skipped", phase="recall", reason="memory lands in stage 2")


async def converse(call: Call, channel, llm, silence_s: float) -> None:
    pack = call.pack
    for question in pack.questions:
        text = await phrase(call, llm, f"{pack.converse} Preguntá sobre: {question.goal}")
        answer = await ask(call, channel, llm, text, silence_s)
        if answer is None:
            await channel.say(pack.goodbye_silent)
            return
        hit = guard.check(pack, answer)
        if hit:
            call.escalated = hit
            call.emit("guard_hit", **hit)
            message = next(f.message for f in pack.red_flags if f.rule == hit["rule"])
            await channel.say(await phrase(call, llm, pack.escalation.format(message=message)))
            return
        call.answers[question.key] = answer
    await channel.say(pack.goodbye)


async def extract(call: Call, channel, llm, silence_s: float) -> None:
    call.emit("phase_skipped", phase="extract", reason="extraction lands in stage 2")


async def store(call: Call, channel, llm, silence_s: float) -> None:
    call.emit("phase_skipped", phase="store", reason="persistence lands in stage 2")


async def summarize(call: Call, channel, llm, silence_s: float) -> None:
    call.summary = await phrase(call, llm, call.pack.summarize)
    call.emit("summary", text=call.summary)


PHASES = (
    ("greet", greet, True),
    ("recall", recall, False),
    ("converse", converse, True),
    ("extract", extract, False),
    ("store", store, False),
    ("summarize", summarize, False),
)


async def run_call(call: Call, channel, llm, silence_s: float = SILENCE_S) -> Call:
    call.emit("call_started", patient=call.patient_name, pack=call.pack.key, memory=call.memory)
    for name, fn, critical in PHASES:
        call.emit("phase_started", phase=name)
        try:
            await fn(call, channel, llm, silence_s)
        except CallEnded:
            call.emit("patient_hung_up", phase=name)
        except Exception as exc:
            call.emit("phase_failed", phase=name, critical=critical, error=repr(exc))
            if critical:
                break
        else:
            call.emit("phase_done", phase=name)
        if name == "converse":
            await channel.close()
    call.emit("call_ended", escalated=bool(call.escalated), answers=dict(call.answers))
    return call
