import re

from app.guard import normalize

# ponytail: 0 to 12 is every reading these packs take — a pain or mood scale stops at ten and
# adherence at seven. A pack that asks for a blood pressure needs this to grow, or the critic
# calls a real reading ungrounded and the re-ask fires on every turn.
SPELLED = {
    "0": ("zero", "cero"),
    "1": ("one", "uno", "una", "once"),
    "2": ("two", "dos", "twice"),
    "3": ("three", "tres"),
    "4": ("four", "cuatro"),
    "5": ("five", "cinco"),
    "6": ("six", "seis"),
    "7": ("seven", "siete"),
    "8": ("eight", "ocho"),
    "9": ("nine", "nueve"),
    "10": ("ten", "diez"),
    "11": ("eleven", "once"),
    "12": ("twelve", "doce"),
}
DIGITS = {word: digit for digit, words in SPELLED.items() for word in words}
NUMBER = re.compile(r"\d+(?:[.,]\d+)?")
TOKEN = re.compile(r"[a-z]+|\d+(?:[.,]\d+)?")


def forms(number: str) -> set[str]:
    return {number, *SPELLED.get(number, ())}


def spoken_in(number: str, haystack: str) -> bool:
    text = normalize(haystack)
    return any(form in text for form in forms(number))


def is_number(token: str) -> bool:
    return token.isdigit() or normalize(token).strip(".,?!") in DIGITS


def numbers_in(text: str) -> list[str]:
    return NUMBER.findall(text)
