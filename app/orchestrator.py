import contextlib

from app import extract, guard
from app.calls import Call
from app.channel import CallEnded
from app.memory import keyterms
from app.packs import ASK_MARKER, GREET_RECALL, memory_block, system_prompt

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


def flagged(call: Call, turns) -> dict | None:
    hit = next((h for t in turns if t and (h := guard.check(call.pack, t))), None)
    if hit:
        call.escalated = hit
        call.emit("guard_hit", **hit)
    return hit


async def escalated(call: Call, channel, llm, answer: str | None) -> bool:
    hit = flagged(call, (*channel.take_dropped(), answer))
    if not hit:
        return False
    message = next(f.message for f in call.pack.red_flags if f.rule == hit["rule"])
    await channel.say(await phrase(call, llm, call.pack.escalation.format(message=message)))
    return True


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
    fragment = call.pack.greet
    if call.facts:
        fragment = f"{fragment} {GREET_RECALL}"
    await channel.say(await phrase(call, llm, fragment))
    # ponytail: the greeting asks the most open question of the call, so it is the likeliest
    # place for an unprompted red flag. Every patient turn is checked, not just the answers.
    await escalated(call, channel, llm, await channel.listen(silence_s))


async def converse(call: Call, channel, llm, store, silence_s: float) -> None:
    if call.escalated:
        return
    pack = call.pack
    goodbye = pack.goodbye
    for question in pack.questions:
        text = await phrase(call, llm, f"{pack.converse} {ASK_MARKER}{question.goal}")
        answer = await ask(call, channel, llm, text, silence_s)
        if await escalated(call, channel, llm, answer):
            return
        if answer is None:
            goodbye = pack.goodbye_silent
            break
        call.answers[question.key] = answer
    interrupted = await channel.say(goodbye)
    # ponytail: only an interrupted goodbye waits for a final turn; waiting after every goodbye
    # adds a full silence window to calls where the patient has already stopped speaking.
    answer = None
    if interrupted:
        with contextlib.suppress(CallEnded):
            answer = await channel.listen(silence_s)
    await escalated(call, channel, llm, answer)


async def extract_facts(call: Call, channel, llm, store, silence_s: float) -> None:
    call.new_facts = await extract.run(call, llm, call.facts)


async def store_facts(call: Call, channel, llm, store, silence_s: float) -> None:
    # ponytail: the call row is not memory. Turning memory off stops the agent from remembering,
    # not from being on the record, and the row has to exist before any fact points at it.
    if store is not None:
        await store.save_call(call)
    if _memory_off(call, "store", store):
        return
    # ponytail: each fact is its own transaction, so a failure part way through keeps the ones
    # already written and drops the rest. Naming them is what this costs; making the whole loop
    # one transaction needs a connection held across statements in app/db.py.
    stored = 0
    try:
        for fact in call.new_facts:
            embedding = await store.embed(fact.fact, call.emit)
            fact_id = await store.insert_fact(call, fact, embedding, fact.supersedes)
            stored += 1
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
                call.emit("fact_superseded", old_id=fact.supersedes, new_id=fact_id)
    except Exception as exc:
        lost = call.new_facts[stored:]
        call.emit(
            "facts_lost",
            count=len(lost),
            stored=stored,
            fact=lost[0].fact if lost else "",
            error=repr(exc),
        )
        raise


async def summarize(call: Call, channel, llm, store, silence_s: float) -> None:
    found = ". ".join(fact.fact for fact in call.new_facts)
    fragment = call.pack.summarize
    if found:
        fragment = f"{fragment} What was recorded: {found}"
    call.summary = await phrase(call, llm, fragment)
    call.emit("summary", text=call.summary)
    if store is not None:
        await store.save_call(call)


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
        failed = False
        try:
            await fn(call, channel, llm, store, silence_s)
        except CallEnded:
            call.emit("patient_hung_up", phase=name)
        except Exception as exc:
            call.emit("phase_failed", phase=name, critical=critical, error=repr(exc))
            failed = critical
        else:
            call.emit("phase_done", phase=name)
        if name == "converse" or failed:
            if not call.escalated:
                flagged(call, channel.take_dropped())
            await channel.close()
            call.ended_at = call.trace[-1]["at"]
        if failed:
            break
    # ponytail: `store` and `summarize` both write the row, and a critical phase breaks out of the
    # loop before either runs — so without this a call that died in `greet` leaves no trace the
    # professional can see. `save_call` is an upsert on the id, so running it again is free.
    if store is not None:
        try:
            await store.save_call(call)
        except Exception as exc:
            call.emit("warning", phase="store", error=repr(exc))
    call.emit("call_ended", escalated=bool(call.escalated), answers=dict(call.answers))
    return call
