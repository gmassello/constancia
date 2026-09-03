import pytest

from app import guard
from app.packs import get_pack

REHAB = get_pack("rehab")

POSITIVES = [
    ("Ayer me caí en el baño", "fall"),
    ("Se me dobló la rodilla bajando la escalera", "fall"),
    ("Sentí un dolor repentino y fuerte en la rodilla", "sudden_sharp_pain"),
    ("Tuve una punzada insoportable el martes", "sudden_sharp_pain"),
    ("Tengo la rodilla hinchada y anoche tuve fiebre", "swelling_with_fever"),
    ("Me quedó el pie con hormigueo todo el día", "numbness"),
    ("TENGO LA PIERNA ENTUMECIDA", "numbness"),
    ("me cai el jueves", "fall"),
]

NEGATIVES = [
    "No, caídas no tuve, nada de eso",
    "La rodilla me duele siete de diez cuando subo escaleras",
    "Hice los ejercicios tres veces, me salté dos días",
    "Después de los ejercicios me queda un poco rígida",
    "Tengo la rodilla un poco hinchada pero sin fiebre ni nada",
    "No me caí ni nada, todo tranquilo",
    "No tuve hormigueo esta semana",
    "Nunca sentí un dolor repentino",
]


@pytest.mark.parametrize(("turn", "rule"), POSITIVES)
def test_red_flags_fire(turn: str, rule: str) -> None:
    hit = guard.check(REHAB, turn)
    assert hit is not None
    assert hit["rule"] == rule
    assert hit["input"] == turn
    assert hit["branch"] == "escalate"
    assert hit["value"]


@pytest.mark.parametrize("turn", NEGATIVES)
def test_ordinary_turns_do_not_fire(turn: str) -> None:
    assert guard.check(REHAB, turn) is None


def test_accents_and_case_do_not_matter() -> None:
    accented = guard.check(REHAB, "ME CAÍ")
    plain = guard.check(REHAB, "me cai")
    assert accented["rule"] == plain["rule"] == "fall"


def test_other_packs_have_their_own_rules() -> None:
    assert guard.check(get_pack("chronic"), "Tengo dolor en el pecho")["rule"] == "chest_pain"
    bleeding = guard.check(get_pack("postpartum"), "Estoy sangrando muchísimo")
    assert bleeding["rule"] == "heavy_bleeding"
