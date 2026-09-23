import re
import unicodedata

from app.packs import VerticalPack

# ponytail: negation is looked for in the 20 characters before the match, and the
# window stops at punctuation or at a conjunction that opens a new clause; a real
# scope parser only if live calls show a missed red flag this cannot reach.
NEGATION = re.compile(
    r"(?:n't|\b(?:no|not|none|nothing|never|without|nor|neither)\b)"
    r"(?:(?!\b(?:but|and|though|although|however|still|yet)\b)[^.,;]){0,20}$"
)


def normalize(text: str) -> str:
    stripped = unicodedata.normalize("NFD", text.lower().replace("\u2019", "'"))
    return "".join(c for c in stripped if unicodedata.category(c) != "Mn")


def _negated(haystack: str, start: int) -> bool:
    return bool(NEGATION.search(haystack[:start]))


WANTS_HUMAN = re.compile(
    r"\b(?:talk|speak) to (?:my|a|an|the) ?(?:real |actual )?"
    r"(?:doctor|physio\w*|midwife|nurse|therapist|person|human|someone)\b"
    r"|\bi want (?:to see |to talk to |to speak to )?(?:a |an |my )?"
    r"(?:real |actual )?(?:doctor|physio\w*|midwife|nurse|person|human)\b"
    r"|\bput me through to\b|\bi need a human\b"
)


def wants_human(patient_turn: str) -> bool:
    # ponytail: this only flags. The terminal decision stays with `check` below, so a patient who
    # asks for their doctor keeps the rest of the call instead of losing it to a hang-up.
    return bool(WANTS_HUMAN.search(normalize(patient_turn)))


def check(pack: VerticalPack, patient_turn: str) -> dict | None:
    haystack = normalize(patient_turn)
    for flag in pack.red_flags:
        for match in re.finditer(flag.pattern, haystack):
            if _negated(haystack, match.start()):
                continue
            return {
                "input": patient_turn,
                "value": match.group(0).strip(),
                "rule": flag.rule,
                "branch": "escalate",
            }
    return None
