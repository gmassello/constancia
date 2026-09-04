from app import extract, guard
from app.calls import Call
from app.channel import CallEnded
from app.memory import keyterms
from app.packs import memory_block, system_prompt

SILENCE_S = 8.0


async def phrase(call: Call, llm, fragment: str) -> str:
    system = system_prompt(call.pack, call.patient_name, fragment, call.memory_prompt)
    return await llm.reply(system, call.history(), call.emit)


async def ask(call: Call, channel, llm, text: str, silence_s: float) -> str | None:
    await channel.say(text)
    answer = await channel.listen(silence_s)
    if answer is None:
        await channel.say(call.pack.reprompt)
        answer = await channel.listen(silence_s)
    return answer


def _memory_off(call: Call, phase: str, store) -> bool:
    if call.memory and store is not None:
        return False
    reason = "memory disabled for this call" if not call.memory else "no memory store configured"
    call.emit("memory_off", phase=phase, reason=reason)
    return True


async def recall(call: Call, channel, llm, store, silence_s: float) -> None:
    if _memory_off(call, "recall", store):
        return
    call.facts = await store.current_facts(call.patient_id)
    call.memory_prompt = memory_block(call.facts)
    terms = keyterms(call.facts, call.pack)
    await channel.set_keyterms(terms)
    call.emit("recall", facts=len(call.facts), keyterms=terms)


async def greet(call: Call, channel, llm, store, silence_s: float) -> None:
    await channel.say(await phrase(call, llm, call.pack.greet))
    await channel.listen(silence_s)


async def converse(call: Call, channel, llm, store, silence_s: float) -> None:
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


async def extract_facts(call: Call, channel, llm, store, silence_s: float) -> None:
    call.new_facts = await extract.run(call, llm, call.facts)


async def store_facts(call: Call, channel, llm, store, silence_s: float) -> None:
    if _memory_off(call, "store", store):
        return
    await store.save_call(call)
    for fact in call.new_facts:
        embedding = await store.embed(fact.fact)
        fact_id = await store.insert_fact(call, fact, embedding)
        call.emit(
            "fact_stored",
            id=fact_id,
            fact=fact.fact,
            term=fact.term,
            category=fact.category,
            value=fact.value,
            quote=fact.quote,
            turn_id=fact.turn_id,
        )
        if fact.supersedes:
            await store.supersede(fact.supersedes, fact_id)
            call.emit("fact_superseded", old_id=fact.supersedes, new_id=fact_id)


async def summarize(call: Call, channel, llm, store, silence_s: float) -> None:
    found = ". ".join(fact.fact for fact in call.new_facts)
    fragment = call.pack.summarize
    if found:
        fragment = f"{fragment} Lo que quedó registrado: {found}"
    call.summary = await phrase(call, llm, fragment)
    call.emit("summary", text=call.summary)


PHASES = (
    ("recall", recall, False),
    ("greet", greet, True),
    ("converse", converse, True),
    ("extract", extract_facts, False),
    ("store", store_facts, False),
    ("summarize", summarize, False),
)


async def run_call(call: Call, channel, llm, store=None, silence_s: float = SILENCE_S) -> Call:
    call.emit("call_started", patient=call.patient_name, pack=call.pack.key, memory=call.memory)
    for name, fn, critical in PHASES:
        call.emit("phase_started", phase=name)
        try:
            await fn(call, channel, llm, store, silence_s)
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
            call.ended_at = call.trace[-1]["at"]
    call.emit("call_ended", escalated=bool(call.escalated), answers=dict(call.answers))
    return call
