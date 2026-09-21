import pytest

from app import guard
from app.packs import get_pack

REHAB = get_pack("rehab")

POSITIVES = [
    ("I fell in the bathroom yesterday", "fall"),
    ("I slipped and fell getting out of the shower", "fall"),
    ("My knee gave out coming down the stairs", "fall"),
    ("I twisted my ankle on the step", "fall"),
    ("I've fallen twice this week", "fall"),
    ("I felt a sudden sharp pain in my knee", "sudden_sharp_pain"),
    ("The pain came on out of nowhere and it was unbearable", "sudden_sharp_pain"),
    ("I had a twinge that was excruciating on Tuesday", "sudden_sharp_pain"),
    ("My knee is swollen and I ran a fever last night", "swelling_with_fever"),
    ("I got a temperature last night and the knee is puffy", "swelling_with_fever"),
    ("My foot has been tingling all day", "numbness"),
    ("MY LEG IS COMPLETELY NUMB", "numbness"),
    ("I can't feel my toes", "numbness"),
    ("There's no feeling in my foot", "numbness"),
]

NEGATIVES = [
    "No, no falls, nothing like that",
    "I haven't fallen at all this week",
    "I have not fallen",
    "I didn't have any tingling this week",
    "I've never had a sudden pain like that",
    "I wasn't numb at any point",
    "There was no numbness or tingling",
    "I'm not in any sudden pain",
    "nothing sudden, just the usual ache",
    "My knee is a little swollen but no fever at all",
    "It's swollen but I don't have a fever",
    "The swelling is down and I've had no temperature",
    "My knee hurts about a seven out of ten on the stairs",
    "I can feel my toes fine now",
    "It feels a bit stiff after the exercises",
    "I fell asleep with the ice pack on",
    "I fell behind on the exercises this week",
    "I did the exercises three times and skipped two days",
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


def test_case_and_apostrophes_do_not_matter() -> None:
    curly = guard.check(REHAB, "I CAN’T FEEL MY TOES")
    straight = guard.check(REHAB, "i can't feel my toes")
    assert curly["rule"] == straight["rule"] == "numbness"


def test_a_rule_that_starts_at_its_own_negator_still_fires() -> None:
    assert guard.check(REHAB, "I can't feel my foot")["rule"] == "numbness"
    assert guard.check(REHAB, "I don't feel any tingling") is None


def test_other_packs_have_their_own_rules() -> None:
    chronic = get_pack("chronic")
    assert guard.check(chronic, "I have pain in my chest")["rule"] == "chest_pain"
    assert guard.check(chronic, "Chest pain since Tuesday")["rule"] == "chest_pain"
    assert guard.check(chronic, "I can't catch my breath on the stairs")["rule"] == "chest_pain"
    assert guard.check(chronic, "I don't have any chest pain") is None

    postpartum = get_pack("postpartum")
    bleeding = [
        "I'm bleeding a lot more than last week",
        "I'm soaking through a pad an hour",
        "The bleeding just won't stop",
        "I'm passing clots",
    ]
    for turn in bleeding:
        assert guard.check(postpartum, turn)["rule"] == "heavy_bleeding"
    assert guard.check(postpartum, "I haven't had any clots") is None
    assert guard.check(postpartum, "I'm not bleeding heavily at all") is None


def test_postpartum_fever_and_headache() -> None:
    postpartum = get_pack("postpartum")
    fever = [
        "yes, I had a fever of thirty nine last night",
        "my temperature went up and I feel shivery",
        "I've had chills since yesterday",
        "I'm running a temperature",
    ]
    for turn in fever:
        assert guard.check(postpartum, turn)["rule"] == "fever"

    headache = [
        "I have had a really bad headache for two days",
        "the worst headache of my life",
        "a pounding headache that will not go away",
    ]
    for turn in headache:
        assert guard.check(postpartum, turn)["rule"] == "bad_headache"

    quiet = [
        "my baby had a fever but I am fine",
        "the baby had a fever",
        "No, no fever, nothing like that",
        "I haven't had a fever",
        "I'm not running a temperature",
        "just a mild headache in the afternoon",
        "no headaches at all this week",
        "I haven't had a bad headache",
    ]
    for turn in quiet:
        assert guard.check(postpartum, turn) is None


def test_chronic_blurred_vision() -> None:
    chronic = get_pack("chronic")
    blurred = [
        "my vision has been blurred since yesterday",
        "everything looks blurry and I feel dizzy",
        "I am seeing double in the mornings",
    ]
    for turn in blurred:
        assert guard.check(chronic, turn)["rule"] == "vision"

    quiet = [
        "no blurred vision at all",
        "I don't have any blurry vision",
        "my sight is fine",
    ]
    for turn in quiet:
        assert guard.check(chronic, turn) is None
