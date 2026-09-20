import pytest

from app import llm


class FakeModels:
    def __init__(self) -> None:
        self.contents = None

    async def generate_content(self, model, contents, config):
        self.contents = contents
        return type(
            "Response", (), {"text": "ok", "usage_metadata": None, "candidates": []}
        )()


def gemini(monkeypatch: pytest.MonkeyPatch) -> tuple[llm.GeminiLLM, FakeModels]:
    models = FakeModels()
    client = type("Client", (), {"aio": type("Aio", (), {"models": models})()})()
    monkeypatch.setattr(llm.GeminiLLM, "__init__", lambda self: None)
    agent = llm.GeminiLLM()
    agent.model = "gemini-test"
    agent.client = client
    return agent, models


async def test_a_history_that_ends_on_the_agent_gets_a_closing_user_turn(monkeypatch) -> None:
    agent, models = gemini(monkeypatch)
    history = [{"role": "model", "text": "Hello Ana, how is your recovery going?"}]

    await agent.reply("system", history)

    assert [c.role for c in models.contents] == ["model", "user"]
    assert models.contents[-1].parts[0].text == llm.SILENT_TURN


async def test_the_placeholder_says_nothing_about_the_call(monkeypatch) -> None:
    loaded = ("end", "call", "over", "goodbye", "bye", "nothing", "silent", "no reply")

    assert not any(word in llm.SILENT_TURN.lower() for word in loaded)


async def test_a_history_that_ends_on_the_patient_is_left_alone(monkeypatch) -> None:
    agent, models = gemini(monkeypatch)
    history = [
        {"role": "model", "text": "How much does it hurt?"},
        {"role": "user", "text": "Seven out of ten."},
    ]

    await agent.reply("system", history)

    assert [c.role for c in models.contents] == ["model", "user"]
    assert models.contents[-1].parts[0].text == "Seven out of ten."


async def test_an_empty_history_opens_the_call(monkeypatch) -> None:
    agent, models = gemini(monkeypatch)

    await agent.reply("system", [])

    assert [c.role for c in models.contents] == ["user"]
    assert models.contents[0].parts[0].text == "(start of the call)"
