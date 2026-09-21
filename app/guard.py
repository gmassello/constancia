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
