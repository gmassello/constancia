import pytest

from app import critic

MEMORY = "right knee pain 7/10 climbing stairs"
HISTORY = [{"role": "user", "text": "I did them three times"}]

SHIPS = [
    "How much does your knee hurt today, from one to ten?",
    "Last week you said 7 out of 10. How is it today?",
    "Good to hear. How many times did you manage the exercises?",
]


@pytest.mark.parametrize("text", SHIPS)
def test_a_short_grounded_question_ships(text: str) -> None:
    assert critic.check(text, MEMORY, HISTORY) is None


def test_an_empty_reply_is_caught() -> None:
    assert critic.check("   ", MEMORY) == "empty reply"


@pytest.mark.parametrize(
    "text",
    [
        "You should increase the dose to two pills. How is that?",
        "Take 400 mg of ibuprofen. Is that better?",
        "I recommend you rest the knee. Does that help?",
        "Stop taking the medication. How does it feel?",
    ],
)
def test_clinical_advice_never_reaches_the_phone(text: str) -> None:
    assert critic.check(text, MEMORY) == "clinical advice"


def test_more_than_two_sentences_is_caught() -> None:
    long = "Hi Ana. Good to hear from you. How is the knee?"
    assert critic.check(long, MEMORY) == "more than two sentences"


def test_a_reply_that_asks_nothing_is_caught() -> None:
    assert critic.check("Thanks for telling me about your week.", MEMORY) == "asks nothing"


def test_a_number_that_is_on_no_file_is_caught() -> None:
    assert critic.check("Last week you said 9 out of 10. How is it now?", MEMORY) == (
        "ungrounded number"
    )


def test_a_number_the_history_carries_is_grounded() -> None:
    assert critic.check("You said 3 sessions. How many this week?", "", HISTORY) is None


def test_with_nothing_on_file_any_number_is_ungrounded() -> None:
    assert critic.check("How is the 7 out of 10 today?", "") == "ungrounded number"
