import pytest
from google.genai import errors

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


class Boom(errors.APIError):
    def __init__(self, code: int) -> None:
        self.code = code


async def test_retrying_backs_off_and_succeeds_on_a_rate_limit(monkeypatch) -> None:
    slept: list[float] = []

    async def no_sleep(seconds: float) -> None:
        slept.append(seconds)

    monkeypatch.setattr(llm.asyncio, "sleep", no_sleep)
    attempts: list[int] = []

    async def flaky():
        attempts.append(1)
        if len(attempts) < 3:
            raise Boom(429)
        return "ok"

    assert await llm.retrying(flaky, "gemini embeddings") == "ok"
    assert slept == [5.0, 10.0]


async def test_retrying_gives_up_on_an_error_that_is_not_retriable() -> None:
    async def refused():
        raise Boom(400)

    with pytest.raises(llm.LLMError) as failure:
        await llm.retrying(refused, "gemini embeddings")

    assert "gemini embeddings failed after 1 attempts: 400" in str(failure.value)
