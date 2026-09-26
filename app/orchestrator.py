import contextlib

from app import critic, extract, guard
from app.calls import Call
from app.channel import CallEnded
from app.memory import keyterms
from app.packs import (
    ANSWER_RELAY,
    ASK_MARKER,
    COMMITMENT_CHECK,
    COMMITMENT_FALLBACK,
    CONFIRM,
    GREET_RECALL,
    Question,
    memory_block,
    system_prompt,
)

SILENCE_S = 8.0


async def phrase(call: Call, llm, fragment: str, fallback: str | None = None) -> str:
    system = system_prompt(call.pack, call.patient_name, fragment, call.memory_prompt)
    text = await llm.reply(system, call.history(), call.emit)
    # ponytail: only a fragment that came with a spoken fallback is criticised, which today means
    # the question loop and nothing else. The greeting, the escalation and the summary have no
    # templated stand-in to fall back to, and inventing one for them would be writing spoken text
    # outside app/packs.py.
    if fallback is None:
        return text
    reason = critic.check(text, call.memory_prompt, call.history())
    if reason is None:
        return text
    call.emit("critic_revise", reason=reason, said=text)
    return fallback


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
    turns = (*channel.take_dropped(), answer)
    for turn in turns:
        if turn and not call.wants_human and guard.wants_human(turn):
            call.wants_human = True
            call.emit("wants_human", quote=turn)
    hit = flagged(call, turns)
    if not hit:
        return False
    message = next(f.message for f in call.pack.red_flags if f.rule == hit["rule"])
    await channel.say(await phrase(call, llm, call.pack.escalation.format(message=message)))
    return True


def doubtful(call: Call) -> list[str]:
    last = call.transcript[-1] if call.transcript else {}
    if last.get("speaker") != "patient":
        return []
    return list(last.get("low_conf") or [])


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


async def deliver_answers(call: Call, channel, store) -> None:
    # ponytail: the professional's sentence is spoken exactly as written, never handed to the
    # model to phrase. That is the whole reason this path exists: the agent must not be able to
    # reword clinical advice, and the panel shows the sentence that will actually be said.
    if store is None or not call.memory or not hasattr(store, "questions"):
        return
    for row in await store.questions(call.patient_id):
        if row["status"] != "answered" or not row["answer"]:
            continue
        await channel.say(ANSWER_RELAY.format(answer=row["answer"]))
        await store.set_question(str(row["id"]), "answered", "delivered")
        call.emit("answer_delivered", question=row["question"], answer=row["answer"])


async def greet(call: Call, channel, llm, store, silence_s: float) -> None:
    fragment = call.pack.greet
    if call.facts:
        fragment = f"{fragment} {GREET_RECALL}"
    await channel.say(await phrase(call, llm, fragment))
    await deliver_answers(call, channel, store)
    # ponytail: the greeting asks the most open question of the call, so it is the likeliest
    # place for an unprompted red flag. Every patient turn is checked, not just the answers.
    await escalated(call, channel, llm, await channel.listen(silence_s))


def questions_for(pack, facts: list[dict]) -> list[Question]:
    # ponytail: the promise check is a question like the others, so it inherits the loop's silence,
    # escalation and answer handling for free. Written as a branch inside the body instead, every
    # one of those three would need its own copy. `app/replay.py` reads the same list to line the
    # scripted replies up, so the two cannot drift.
    questions = list(pack.questions)
    if any(fact.get("category") == "commitment" for fact in facts):
        at = next((i for i, q in enumerate(questions) if q.key == "adherence"), 0)
        questions.insert(at, Question("commitment", COMMITMENT_CHECK, COMMITMENT_FALLBACK))
    return questions


async def converse(call: Call, channel, llm, store, silence_s: float) -> None:
    if call.escalated:
        return
    pack = call.pack
    goodbye = pack.goodbye
    for question in questions_for(pack, call.facts):
        fragment = f"{pack.converse} {ASK_MARKER}{question.goal}"
        text = await phrase(call, llm, fragment, question.fallback)
        answer = await ask(call, channel, llm, text, silence_s)
        if await escalated(call, channel, llm, answer):
            return
        if answer is None:
            goodbye = pack.goodbye_silent
            break
        call.answers[question.key] = answer
        # ponytail: the confirmation is spoken as written rather than phrased by the model. It is
        # one turn on a phone line and the point of it is to read a number back unchanged, which
        # is the one thing a rewording could lose.
        heard = doubtful(call)
        if heard:
            call.emit("low_confidence", words=heard, question=question.key)
            back = CONFIRM.format(value=" or ".join(heard))
            reply = await ask(call, channel, llm, back, silence_s)
            if await escalated(call, channel, llm, reply):
                return
    interrupted = await channel.say(goodbye)
    # ponytail: only an interrupted goodbye waits for a final turn; waiting after every goodbye
    # adds a full silence window to calls where the patient has already stopped speaking.
    answer = None
    if interrupted:
        with contextlib.suppress(CallEnded):
            answer = await channel.listen(silence_s)
    await escalated(call, channel, llm, answer)


async def extract_facts(call: Call, channel, llm, store, silence_s: float) -> None:
    call.new_facts, call.new_questions = await extract.run(call, llm, call.facts)


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
    for question in call.new_questions:
        question_id = await store.insert_question(call, question)
        call.emit(
            "question_stored",
            id=question_id,
            question=question.question,
            quote=question.quote,
            turn_id=question.turn_id,
        )


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
    # ponytail: only a hang-up seen inside a phase stops the next live one. A patient who answers
    # the greeting and then hangs up still costs `converse` one question from the model, because
    # `hung_up` waits for the STT flush; cutting on Twilio's `stop` instead would lose that turn.
    ended = False
    for name, fn, critical in PHASES:
        call.emit("phase_started", phase=name)
        failed = False
        try:
            if ended and critical:
                raise CallEnded
            await fn(call, channel, llm, store, silence_s)
        except CallEnded:
            ended = True
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
    call.emit(
        "call_ended",
        escalated=bool(call.escalated),
        wants_human=call.wants_human,
        answers=dict(call.answers),
    )
    return call
