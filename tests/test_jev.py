import httpx
import pytest

from app import jev

REQUIRED = (
    "GEMINI_API_KEY",
    "ASSEMBLYAI_API_KEY",
    "ELEVENLABS_API_KEY",
    "ELEVENLABS_VOICE_ID",
    "TWILIO_ACCOUNT_SID",
    "TWILIO_AUTH_TOKEN",
    "PUBLIC_BASE_URL",
)
QUOTE = "I will log my blood pressure every morning"
TOKEN = "gateway-test-key"


def keyed(monkeypatch: pytest.MonkeyPatch) -> None:
    from app.config import get_settings

    for name in REQUIRED:
        monkeypatch.setenv(name, "x")
    monkeypatch.setenv("TWILIO_NUMBER", "+541199999999")
    monkeypatch.setenv("AI_GATEWAY_API_KEY", TOKEN)
    get_settings.cache_clear()


def answering(monkeypatch: pytest.MonkeyPatch, handler) -> dict:
    sent: dict = {}

    class FakeClient:
        def __init__(self, *args, **kwargs) -> None:
            sent["timeout"] = kwargs.get("timeout")

        async def __aenter__(self):
            return self

        async def __aexit__(self, *args) -> None:
            return None

        async def post(self, url, **kwargs):
            sent["url"] = url
            sent["json"] = kwargs.get("json")
            sent["headers"] = kwargs.get("headers")
            return handler()

    monkeypatch.setattr("app.jev.httpx.AsyncClient", FakeClient)
    return sent


REQUEST = httpx.Request("POST", jev.ENDPOINT)


def replied(status: int, **body) -> httpx.Response:
    return httpx.Response(status, request=REQUEST, **body)


def probability(value) -> httpx.Response:
    return replied(200, json={"answers": {"commits": {"probability": value}}})


async def test_no_key_answers_none_without_touching_the_network(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class Exploding:
        def __init__(self, *args, **kwargs) -> None:
            raise AssertionError("the gate let a keyless call reach the network")

    monkeypatch.setattr("app.jev.httpx.AsyncClient", Exploding)

    assert await jev.commits(QUOTE) is None


async def test_a_probability_over_the_floor_comes_back(monkeypatch: pytest.MonkeyPatch) -> None:
    keyed(monkeypatch)
    answering(monkeypatch, lambda: probability(0.94))

    assert await jev.commits(QUOTE) == 0.94


async def test_a_probability_under_the_floor_is_not_a_commitment(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    keyed(monkeypatch)
    answering(monkeypatch, lambda: probability(0.62))

    assert await jev.commits(QUOTE) is None


async def test_the_floor_is_the_configured_one(monkeypatch: pytest.MonkeyPatch) -> None:
    keyed(monkeypatch)
    monkeypatch.setenv("JEV_FLOOR", "0.5")
    from app.config import get_settings

    get_settings.cache_clear()
    answering(monkeypatch, lambda: probability(0.62))

    assert await jev.commits(QUOTE) == 0.62


def test_the_question_and_its_rubric_reach_the_payload() -> None:
    # The wording is the knob `scripts/smoke_jev.py` measures, and nothing else in the suite touches
    # it: deleting `CRITERIA` used to leave every test green while the model was asked a boolean
    # with no rubric at all. This does not measure aim — that needs the network — it only keeps the
    # question from going out empty.
    question = jev.payload("I will do the exercises")["questions"][jev.KEY]

    assert question["instructions"] == jev.INSTRUCTIONS
    assert question["criteria"] == jev.CRITERIA
    assert set(jev.CRITERIA) == {"true", "false"}
    assert all(len(value) > 40 for value in jev.CRITERIA.values())
    assert len(jev.INSTRUCTIONS) > 100


async def test_only_the_quote_crosses_the_boundary(monkeypatch: pytest.MonkeyPatch) -> None:
    keyed(monkeypatch)
    sent = answering(monkeypatch, lambda: probability(0.94))

    await jev.commits(QUOTE)

    assert sent["url"] == jev.ENDPOINT
    assert sent["json"]["state"] == QUOTE
    assert sent["json"]["model"] == "typesafe-ai/jev"
    assert sent["json"]["questions"]["commits"]["type"] == "boolean"
    assert set(sent["json"]) == {"model", "state", "questions", "providerOptions"}
    assert sent["json"]["providerOptions"]["gateway"] == {"only": [jev.PROVIDER]}
    assert sent["headers"]["Authorization"] == f"Bearer {TOKEN}"
    assert sent["timeout"] == jev.TIMEOUT_S

    from app.config import get_settings

    monkeypatch.setenv("JEV_ZERO_RETENTION", "true")
    get_settings.cache_clear()
    await jev.commits(QUOTE)

    assert sent["json"]["providerOptions"]["gateway"]["zeroDataRetention"] is True


async def test_a_refusal_answers_none(monkeypatch: pytest.MonkeyPatch) -> None:
    keyed(monkeypatch)
    answering(monkeypatch, lambda: replied(500, text="upstream is down"))

    assert await jev.commits(QUOTE) is None


async def test_a_timeout_answers_none(monkeypatch: pytest.MonkeyPatch) -> None:
    keyed(monkeypatch)

    def slow():
        raise httpx.ConnectTimeout("took too long")

    answering(monkeypatch, slow)

    assert await jev.commits(QUOTE) is None


async def test_a_body_that_is_not_json_answers_none(monkeypatch: pytest.MonkeyPatch) -> None:
    keyed(monkeypatch)
    answering(monkeypatch, lambda: replied(200, text="<html>gateway</html>"))

    assert await jev.commits(QUOTE) is None


async def test_a_renamed_field_answers_none(monkeypatch: pytest.MonkeyPatch) -> None:
    keyed(monkeypatch)
    answering(monkeypatch, lambda: replied(200, json={"answers": {"commits": {"noul": 0.94}}}))

    assert await jev.commits(QUOTE) is None


async def test_a_probability_outside_zero_to_one_answers_none(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    keyed(monkeypatch)
    answering(monkeypatch, lambda: probability(42))

    assert await jev.commits(QUOTE) is None


async def test_a_probability_that_is_not_a_number_answers_none(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    keyed(monkeypatch)
    answering(monkeypatch, lambda: probability("very likely"))

    assert await jev.commits(QUOTE) is None
