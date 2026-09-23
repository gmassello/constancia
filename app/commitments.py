import re

from app.guard import normalize

BASE = 0.65
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
ACTION = re.compile(
    r"\b(?:do|doing|start|starting|keep|keeping)\b[^.]{0,24}"
    r"\b(?:exercis\w*|routine|stretch\w*|physio\w*|therapy|sessions?|them|it|these)\b"
    r"|\b(?:walk|walking|stretch|stretching|exercise|exercising|rest|resting"
    r"|swim|swimming|ice|elevate|elevating)\b"
    r"|\btake\b[^.]{0,24}\b(?:medication|pills?|tablets?|dose|doses|painkillers?)\b"
    r"|\bgo(?: back)? to\b[^.]{0,24}\b(?:physio\w*|appointment|session|clinic|doctor|gym|pool)\b"
    r"|\b(?:keep up|stick to|stay off|build up)\b"
)
DEADLINE = re.compile(
    r"\b(?:today|tonight|tomorrow|this (?:week|weekend|evening|morning|afternoon)|next week)\b"
    r"|\b(?:every|each) (?:day|morning|night|evening|other day)\b"
    r"|\bon (?:monday|tuesday|wednesday|thursday|friday|saturday|sunday)s?\b"
    r"|\b(?:daily|twice a day|\w+ times a (?:day|week))\b"
    r"|\bbefore (?:bed|breakfast|dinner|my next)\b"
)
HEDGE = re.compile(
    r"\b(?:maybe|might|probably|hopefully|i guess|i suppose|i hope)\b"
    r"|\bif i (?:have time|can|remember|feel|manage)\b"
    r"|\btry to\b|\bsee if i\b|\bshould be able\b"
)
ASK = re.compile(r"\b(?:can|could|would|will) you\b|\bplease\b|\bwould you mind\b")


def confidence(quote: str) -> float | None:
    text = normalize(quote)
    if ASK.search(text) and not PLEDGE.search(text):
        return None
    if not PLEDGE.search(text) or not ACTION.search(text):
        return None
    score = BASE + (DEADLINE_BONUS if DEADLINE.search(text) else 0.0)
    if HEDGE.search(text):
        score -= HEDGE_PENALTY
    return round(score, 2) if score >= FLOOR else None
