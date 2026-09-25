import re
from functools import lru_cache

from app import jev
from app.guard import normalize

BASE = 0.65
RECALLED = 0.5
DEADLINE_BONUS = 0.25
HEDGE_PENALTY = 0.35
FLOOR = 0.4

SUBJECT = r"(?:i|we)"
PLEDGE = re.compile(
    rf"\b{SUBJECT}'?ll\b"
    rf"|\b{SUBJECT} will\b"
    rf"|\b{SUBJECT}\s*(?:am|'m|are|'re)\s+(?:going to|gonna)\b"
    rf"|\b{SUBJECT} (?:promise|plan|intend) to\b"
    r"|\blet me\b"
)
# ponytail: the verbs every vertical shares. What a patient promises to *do* is clinical content, so
# the rest lives in `pack.actions` next to the red flags and the measures; this half is here because
# duplicating it into three packs would be the same list three times. A promise no enumeration
# reaches — "I'll take the pram to the corner every afternoon" — is what `recall` is for.
GENERIC_ACTION = (
    r"\b(?:do|doing|start|starting|keep|keeping)\b[^.]{0,24}\b(?:them|it|these|that)\b"
    r"|\b(?:rest|resting|walk|walking)\b"
    r"|\btake\b[^.]{0,24}\b(?:medication|meds|pills?|tablets?|dose|doses|painkillers?)\b"
    r"|\bgo(?: back)? to\b[^.]{0,24}\b(?:appointment|check-?up|clinic|doctor|nurse|hospital)\b"
    r"|\b(?:keep up|stick to|stay off|build up|cut down)\b"
)


@lru_cache
def _action(actions: str) -> re.Pattern[str]:
    return re.compile(f"{GENERIC_ACTION}|{actions}")
DEADLINE = re.compile(
    r"\b(?:today|tonight|tomorrow|this (?:week|weekend|evening|morning|afternoon)|next week)\b"
    r"|\b(?:every|each) (?:single )?(?:day|week|morning|afternoon|evening|night|other day)\b"
    r"|\bon (?:monday|tuesday|wednesday|thursday|friday|saturday|sunday)s?\b"
    r"|\b(?:daily|twice a day|\w+ times a (?:day|week))\b"
    r"|\bbefore (?:bed|breakfast|lunch|dinner|my next)\b"
)
HEDGE = re.compile(
    r"\b(?:maybe|might|probably|hopefully|i guess|i suppose|i hope)\b"
    r"|\bif i (?:have time|can|remember|feel|manage)\b"
    r"|\btry to\b|\bsee if i\b|\bshould be able\b"
)

def _score(text: str, base: float) -> float | None:
    score = base + (DEADLINE_BONUS if DEADLINE.search(text) else 0.0)
    if HEDGE.search(text):
        score -= HEDGE_PENALTY
    return round(score, 2) if score >= FLOOR else None


def confidence(quote: str, pack) -> float | None:
    text = normalize(quote)
    if not PLEDGE.search(text) or not _action(pack.actions).search(text):
        return None
    return _score(text, BASE)


async def recall(quote: str, emit=None) -> float | None:
    # ponytail: only the action vocabulary is delegated — never the score, and never the pledge. The
    # vocabulary is enumerated per vertical in `pack.actions`, and an enumeration always has an edge
    # ("I'll take the pram to the corner every afternoon" is a promise no list reaches). PLEDGE,
    # DEADLINE and HEDGE are generic English, so they stay here and keep a deterministic floor under
    # the model: a sentence with no first-person pledge never reaches the network at all, which is
    # both the cheaper answer and one less patient sentence leaving the machine. Jev is documented
    # as weak on counting and dates, and its own README says the probabilities need calibrating
    # against your own data first, so the number is still ours and a model-only promise scores less.
    # Upgrade path: once smoke-jev has enough calls to calibrate against, the probability can
    # replace RECALLED.
    text = normalize(quote)
    if not PLEDGE.search(text):
        return None
    if await jev.commits(quote, emit) is None:
        return None
    return _score(text, RECALLED)
