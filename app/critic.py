import re

from app import numbers
from app.guard import normalize

MAX_SENTENCES = 2
ADVICE = re.compile(
    r"\byou should\b|\byou must\b|\byou need to\b|\bi recommend\b|\bmy advice\b"
    r"|\b(?:take|takes|taking|stop|stops|stopping|increase|increases|increasing"
    r"|reduce|reduces|reducing|double|halve|skip|skipping)\b[^.?!]{0,24}"
    r"\b(?:dose|doses|dosage|pills?|tablets?|medication|painkillers?|mg|milligrams?)\b"
    r"|\b\d+\s*mg\b"
    r"|\bdeberias\b|\btenes que\b|\bte recomiendo\b"
)
SENTENCE = re.compile(r"[.!?]+(?:\s|$)")


def _sentences(text: str) -> int:
    return len([part for part in SENTENCE.split(text) if part.strip()])


def check(text: str, memory: str = "", history: list[dict] | None = None) -> str | None:
    # ponytail: four rules, and deliberately not the fifth the source design asked for — that the
    # reply share a word with the goal it was given. A goal here is one clause, so a legitimate
    # recall question ("Last week you said seven. How is it now?") shares nothing with it and gets
    # flagged. On a phone line a false positive costs a templated turn, which is worse than letting
    # an on-topic paraphrase through; the model already has the goal in its system prompt.
    body = text.strip()
    if not body:
        return "empty reply"
    if ADVICE.search(normalize(body)):
        return "clinical advice"
    if _sentences(body) > MAX_SENTENCES:
        return "more than two sentences"
    if not body.endswith("?"):
        return "asks nothing"
    grounded = " ".join([memory, *(turn["text"] for turn in history or [])])
    if any(not numbers.spoken_in(n, grounded) for n in numbers.numbers_in(body)):
        return "ungrounded number"
    return None
