import json
from pathlib import Path

from app import analysis
from app.calls import Call
from app.memory import load_seed
from app.packs import get_pack

PAYLOAD = json.loads((Path(__file__).parent / "fixtures" / "aai_transcript.json").read_text())
RECORDING = "https://api.twilio.com/2010-04-01/Accounts/AC/Recordings/RE"


def build() -> Call:
    call = Call(patient_id="p", patient_name="Ana", pack=get_pack("rehab"))
    call.recording_url = RECORDING
    return call


def test_the_request_asks_for_every_feature_the_panel_shows() -> None:
    body = analysis.request_body(RECORDING, "es")

    assert body["audio_url"] == RECORDING
    assert body["language_code"] == "es"
    assert body["punctuate"] and body["entity_detection"] and body["sentiment_analysis"]


def test_summarize_keeps_entities_and_counts_sentiment() -> None:
    summary = analysis.summarize(PAYLOAD)

    assert summary["transcript_id"] == "t-abc123"
    assert [e["text"] for e in summary["entities"]] == ["rodilla derecha", "siete de diez"]
    assert summary["sentiment"] == {"NEGATIVE": 2, "NEUTRAL": 1}
    assert [n["confidence"] for n in summary["negative"]] == [0.91, 0.64]


def test_summarize_survives_a_transcript_with_no_entities() -> None:
    summary = analysis.summarize({"id": "t", "entities": None})

    assert summary["entities"] == []
    assert summary["sentiment"] == {}
    assert summary["negative"] == []


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


async def test_run_never_propagates_a_failure() -> None:
    call = build()

    async def boom(url: str) -> dict:
        raise RuntimeError("assemblyai is down")

    await analysis.run(call, None, boom)

    assert [e["type"] for e in call.trace] == ["analysis_failed"]
    assert "assemblyai is down" in call.trace[0]["error"]
