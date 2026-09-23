import json
from pathlib import Path

from app import analysis
from app.calls import Call
from app.memory import load_seed
from app.packs import get_pack

PAYLOAD = json.loads((Path(__file__).parent / "fixtures" / "aai_transcript.json").read_text())
RECORDING = "https://api.twilio.com/2010-04-01/Accounts/AC/Recordings/RE"
ENV = {
    "GEMINI_API_KEY": "x",
    "ASSEMBLYAI_API_KEY": "x",
    "ELEVENLABS_API_KEY": "x",
    "ELEVENLABS_VOICE_ID": "x",
    "TWILIO_ACCOUNT_SID": "AC",
    "TWILIO_AUTH_TOKEN": "tok",
    "TWILIO_NUMBER": "+541199999999",
    "PUBLIC_BASE_URL": "https://constancia.example.com",
}


def build() -> Call:
    call = Call(patient_id="p", patient_name="Ana", pack=get_pack("rehab"))
    call.recording_url = RECORDING
    return call


def test_the_request_asks_for_every_feature_the_panel_shows() -> None:
    body = analysis.request_body(RECORDING, "en")

    assert body["audio_url"] == RECORDING
    assert body["language_code"] == "en"
    assert body["punctuate"] and body["entity_detection"] and body["sentiment_analysis"]


def test_summarize_keeps_entities_and_counts_sentiment() -> None:
    summary = analysis.summarize(PAYLOAD)

    assert summary["transcript_id"] == "t-abc123"
    assert [e["text"] for e in summary["entities"]] == ["right knee", "seven out of ten"]
    assert summary["sentiment"] == {"NEGATIVE": 2, "NEUTRAL": 1}
    assert [n["confidence"] for n in summary["negative"]] == [0.91, 0.64]


def test_summarize_survives_a_transcript_with_no_entities() -> None:
    summary = analysis.summarize({"id": "t", "entities": None})

    assert summary["entities"] == []
    assert summary["sentiment"] == {}
    assert summary["negative"] == []


async def test_a_twilio_recording_is_relayed_instead_of_handed_over(monkeypatch) -> None:
    import httpx

    from app.config import get_settings

    for key, value in ENV.items():
        monkeypatch.setenv(key, value)
    get_settings.cache_clear()
    seen = {}

    async def handler(request: httpx.Request) -> httpx.Response:
        if request.url.host == "api.twilio.com":
            seen["auth"] = request.headers.get("authorization", "")
            seen["path"] = request.url.path
            return httpx.Response(200, content=b"ID3fake-mp3")
        seen["uploaded"] = request.content
        return httpx.Response(200, json={"upload_url": "https://cdn.assemblyai.com/u/1"})

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        url = await analysis.hosted(client, RECORDING, {"authorization": "k"})

    assert url == "https://cdn.assemblyai.com/u/1"
    assert seen["path"].endswith(".mp3")
    assert seen["auth"].startswith("Basic ")
    assert seen["uploaded"] == b"ID3fake-mp3"
    get_settings.cache_clear()


async def test_a_url_that_is_not_twilios_is_passed_straight_through(
    monkeypatch,
) -> None:
    import httpx

    from app.config import get_settings

    for key in ENV:
        monkeypatch.delenv(key, raising=False)
    monkeypatch.chdir("/")
    get_settings.cache_clear()

    async def handler(request: httpx.Request) -> httpx.Response:
        raise AssertionError("nothing should be fetched")

    try:
        async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
            url = await analysis.hosted(client, "https://example.com/a.mp3", {})
    finally:
        get_settings.cache_clear()

    assert url == "https://example.com/a.mp3"


async def test_run_emits_the_event_and_writes_the_analysis() -> None:
    call = build()
    store = load_seed()
    await store.save_call(call)

    async def fetch(url: str) -> dict:
        assert url == RECORDING
        return PAYLOAD

    await analysis.run(call, store, fetch)

    event = next(e for e in call.trace if e["type"] == "analysis_ready")
    assert event["entities"] == 2
    assert event["sentiment"] == {"NEGATIVE": 2, "NEUTRAL": 1}
    assert (await store.call(call.id))["analysis"]["transcript_id"] == "t-abc123"


async def test_an_analysis_with_no_call_row_to_attach_it_to_says_so() -> None:
    call = build()
    store = load_seed()

    async def fetch(url: str) -> dict:
        return PAYLOAD

    await analysis.run(call, store, fetch)

    warnings = [e for e in call.trace if e["type"] == "warning"]
    assert [w["phase"] for w in warnings] == ["analysis"]
    assert await store.call(call.id) is None


async def test_run_never_propagates_a_failure() -> None:
    call = build()

    async def boom(url: str) -> dict:
        raise RuntimeError("assemblyai is down")

    await analysis.run(call, None, boom)

    assert [e["type"] for e in call.trace] == ["analysis_failed"]
    assert "assemblyai is down" in call.trace[0]["error"]


SPOKEN = "My right knee hurts seven out of ten, especially when I climb stairs."
WORDS = [
    {"text": word, "start": i * 400, "end": i * 400 + 380}
    for i, word in enumerate(SPOKEN.split())
]


def test_a_verbatim_quote_lands_on_the_words_that_carry_it() -> None:
    assert analysis.locate("hurts seven out of ten", WORDS) == (1200, 3180)


def test_punctuation_and_case_do_not_move_the_span() -> None:
    assert analysis.locate("HURTS seven, out of ten!", WORDS) == (1200, 3180)


def test_a_quote_the_recording_does_not_carry_gets_no_span() -> None:
    assert analysis.locate("I fell in the bathroom", WORDS) is None


def test_an_empty_quote_gets_no_span() -> None:
    assert analysis.locate("   ", WORDS) is None


def test_a_quote_longer_than_the_recording_gets_no_span() -> None:
    assert analysis.locate(SPOKEN, WORDS[:3]) is None


async def test_run_anchors_the_facts_it_can_place() -> None:
    from app.extract import Fact

    call = build()
    store = load_seed()
    call.transcript = [{"turn_id": 1, "speaker": "patient", "text": SPOKEN}]
    await store.save_call(call)
    fact = Fact(
        fact="right knee pain 7/10",
        term="right knee",
        category="symptom",
        value=7,
        quote="hurts seven out of ten",
        turn_id=1,
    )
    fact_id = await store.insert_fact(call, fact, [0.0, 1.0])

    async def fetch(url: str) -> dict:
        return {**PAYLOAD, "words": WORDS}

    await analysis.run(call, store, fetch)

    anchored = next(row for row in store.facts if row["id"] == fact_id)
    assert (anchored["start_ms"], anchored["end_ms"]) == (1200, 3180)
    assert [e["facts"] for e in call.trace if e["type"] == "quotes_anchored"] == [1]


async def test_a_payload_with_no_word_timings_anchors_nothing() -> None:
    call = build()
    store = load_seed()
    await store.save_call(call)

    async def fetch(url: str) -> dict:
        return PAYLOAD

    await analysis.run(call, store, fetch)

    assert [e for e in call.trace if e["type"] == "quotes_anchored"] == []
