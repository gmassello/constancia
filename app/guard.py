import re
import unicodedata

from app.packs import VerticalPack

# ponytail: negation is looked for in the 20 characters before the match;
# a real scope parser only if live calls show false positives.
NEGATION = re.compile(r"\b(no|sin|nunca|tampoco)\b[^.,;]{0,20}$")


def normalize(text: str) -> str:
    stripped = unicodedata.normalize("NFD", text.lower())
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
