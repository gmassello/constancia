import pytest

from app import commitments

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
    assert commitments.confidence(quote) is not None


@pytest.mark.parametrize("quote", NOT_PROMISES)
def test_what_is_not_a_promise_scores_nothing(quote: str) -> None:
    assert commitments.confidence(quote) is None


def test_a_deadline_raises_the_score() -> None:
    dated = commitments.confidence("I will walk every morning")
    undated = commitments.confidence("I will walk")
    assert dated is not None and undated is not None and dated > undated


def test_hedging_lowers_the_score() -> None:
    plain = commitments.confidence("I will walk tomorrow")
    hedged = commitments.confidence("Maybe I will walk tomorrow")
    assert plain is not None and hedged is not None and hedged < plain


def test_a_hedge_with_no_deadline_falls_under_the_floor() -> None:
    assert commitments.confidence("Maybe I will walk") is None


def test_a_request_that_also_pledges_survives() -> None:
    assert commitments.confidence("Can you send the video, I will do the exercises tonight")


def test_grounding_is_case_and_accent_insensitive() -> None:
    assert commitments.confidence("I WILL WALK EVERY MORNING") is not None
