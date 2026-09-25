import pytest

from app import commitments
from app.packs import get_pack

REHAB = get_pack("rehab")

PROMISES = [
    "I will do the exercises every day this week",
    "I'm going to walk every morning",
    "We are going to keep up the routine",
    "I will stretch before bed",
    "I'll take the painkillers twice a day",
    "I'm going to go back to physio on Monday",
]

NOT_PROMISES = [
    "Can you send me the video?",
    "Could you please remind me to stretch?",
    "My physio said I should walk more",
    "I usually walk on Sundays",
    "I'll be at the conference next week",
    "I did the exercises three times",
    "The exercises are hard",
    "I'll try to walk if I have time",
]


@pytest.mark.parametrize("quote", PROMISES)
def test_a_first_person_promise_with_an_action_scores(quote: str) -> None:
    assert commitments.confidence(quote, REHAB) is not None


@pytest.mark.parametrize("quote", NOT_PROMISES)
def test_what_is_not_a_promise_scores_nothing(quote: str) -> None:
    assert commitments.confidence(quote, REHAB) is None


def test_a_deadline_raises_the_score() -> None:
    dated = commitments.confidence("I will walk every morning", REHAB)
    undated = commitments.confidence("I will walk", REHAB)
    assert dated is not None and undated is not None and dated > undated


def test_the_four_parts_of_the_day_are_all_deadlines() -> None:
    scores = {
        part: commitments.confidence(f"I will walk every {part}", REHAB)
        for part in ("morning", "afternoon", "evening", "night")
    }
    undated = commitments.confidence("I will walk", REHAB)
    assert undated is not None
    assert set(scores.values()) == {undated + commitments.DEADLINE_BONUS}


def test_hedging_lowers_the_score() -> None:
    plain = commitments.confidence("I will walk tomorrow", REHAB)
    hedged = commitments.confidence("Maybe I will walk tomorrow", REHAB)
    assert plain is not None and hedged is not None and hedged < plain


def test_a_hedge_with_no_deadline_falls_under_the_floor() -> None:
    assert commitments.confidence("Maybe I will walk", REHAB) is None


def test_a_request_that_also_pledges_survives() -> None:
    assert commitments.confidence("Can you send the video, I will do the exercises tonight", REHAB)


def test_grounding_is_case_and_accent_insensitive() -> None:
    assert commitments.confidence("I WILL WALK EVERY MORNING", REHAB) is not None


OTHER_PACKS = [
    ("I will feed him on both sides every night", "postpartum"),
    ("I am going to check my sugar before breakfast", "chronic"),
    ("I will log my blood pressure every morning", "chronic"),
]

# A promise no enumeration reaches, in any pack: the action is
# ordinary life rather than clinical vocabulary.
UNENUMERABLE = [
    "I will take the pram to the corner every morning",
    "I will wear the compression stockings every day",
    "I am going to sit with my mother every evening",
]


def answering(monkeypatch: pytest.MonkeyPatch, probability: float | None) -> list[str]:
    asked: list[str] = []

    async def commits(quote: str, emit=None) -> float | None:
        asked.append(quote)
        return probability

    monkeypatch.setattr("app.commitments.jev.commits", commits)
    return asked


@pytest.mark.parametrize(("quote", "key"), OTHER_PACKS)
def test_a_promise_is_scored_by_the_vocabulary_of_its_own_pack(quote: str, key: str) -> None:
    assert commitments.confidence(quote, get_pack(key)) is not None
    assert commitments.confidence(quote, REHAB) is None


@pytest.mark.parametrize("quote", UNENUMERABLE)
async def test_the_second_opinion_rescues_what_no_pack_enumerates(
    quote: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    for key in ("rehab", "postpartum", "chronic"):
        assert commitments.confidence(quote, get_pack(key)) is None
    answering(monkeypatch, 0.96)

    assert await commitments.recall(quote) == commitments.RECALLED + commitments.DEADLINE_BONUS


async def test_a_rescued_promise_scores_below_one_the_vocabulary_matched(
    monkeypatch: pytest.MonkeyPatch
) -> None:
    answering(monkeypatch, 0.96)
    matched = commitments.confidence("I will walk every morning", REHAB)

    assert await commitments.recall("I will log my blood pressure every morning") < matched


async def test_a_second_opinion_that_says_no_changes_nothing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    answering(monkeypatch, None)

    assert await commitments.recall("I will log my blood pressure every morning") is None


@pytest.mark.parametrize("quote", NOT_PROMISES)
async def test_the_second_opinion_is_never_asked_without_a_first_person_pledge(
    quote: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    asked = answering(monkeypatch, 0.99)
    scored = await commitments.recall(quote)

    if commitments.PLEDGE.search(commitments.normalize(quote)):
        assert asked == [quote]
    else:
        assert scored is None and asked == []


async def test_a_hedged_rescue_falls_under_the_floor(monkeypatch: pytest.MonkeyPatch) -> None:
    answering(monkeypatch, 0.99)

    assert await commitments.recall("Maybe I will check my sugar") is None
