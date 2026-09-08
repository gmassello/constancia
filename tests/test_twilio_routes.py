import pytest
from fastapi.testclient import TestClient
from twilio.request_validator import RequestValidator

BASE_URL = "https://constancia.example.com"
AUTH_TOKEN = "test-auth-token"

ENV = {
    "GEMINI_API_KEY": "x",
    "ASSEMBLYAI_API_KEY": "x",
    "ELEVENLABS_API_KEY": "x",
    "ELEVENLABS_VOICE_ID": "x",
    "TWILIO_ACCOUNT_SID": "x",
    "TWILIO_AUTH_TOKEN": AUTH_TOKEN,
    "TWILIO_NUMBER": "+541199999999",
    "PUBLIC_BASE_URL": BASE_URL,
    "VALIDATE_TWILIO_SIGNATURE": "true",
}


@pytest.fixture
def client(monkeypatch: pytest.MonkeyPatch) -> TestClient:
    from app.calls import CALLS
    from app.config import get_settings
    from app.main import app

    for key, value in ENV.items():
        monkeypatch.setenv(key, value)
    get_settings.cache_clear()
    CALLS.clear()
    with TestClient(app) as client:
        yield client
    get_settings.cache_clear()


@pytest.fixture
def call():
    from app.calls import Call, register
    from app.packs import get_pack

    return register(Call(patient_id="test", patient_name="Ana", pack=get_pack("rehab")))


def signed(path: str, params: dict) -> dict:
    signature = RequestValidator(AUTH_TOKEN).compute_signature(f"{BASE_URL}{path}", params)
    return {"X-Twilio-Signature": signature}


def test_voice_returns_a_bidirectional_stream(client: TestClient, call) -> None:
    path = f"/voice?call_id={call.id}"
    response = client.post(path, data={}, headers=signed(path, {}))

    assert response.status_code == 200
    assert "<Connect>" in response.text
    assert f'<Stream url="wss://constancia.example.com/media/{call.id}"' in response.text


def test_voice_rejects_a_bad_signature(client: TestClient, call) -> None:
    response = client.post(
        f"/voice?call_id={call.id}", data={}, headers={"X-Twilio-Signature": "nope"}
    )
    assert response.status_code == 403


def test_voice_rejects_an_unknown_call(client: TestClient) -> None:
    path = "/voice?call_id=does-not-exist"
    response = client.post(path, data={}, headers=signed(path, {}))
    assert response.status_code == 404


def test_recording_callback_rejects_a_foreign_url(client: TestClient, call) -> None:
    form = {"CallSid": "CA123", "RecordingUrl": "https://evil.example.com/audio.wav"}
    response = client.post("/voice/recording", data=form, headers=signed("/voice/recording", form))
    assert response.status_code == 400


def test_recording_callback_stores_a_twilio_url(client: TestClient, call) -> None:
    call.twilio_sid = "CA123"
    url = "https://api.twilio.com/2010-04-01/Accounts/AC1/Recordings/RE1"
    form = {"CallSid": "CA123", "RecordingUrl": url}
    response = client.post("/voice/recording", data=form, headers=signed("/voice/recording", form))

    assert response.status_code == 204
    assert call.recording_url == url


def test_health_needs_no_signature(client: TestClient) -> None:
    assert client.get("/health").json()["status"] == "ok"


def test_trace_returns_the_event_stream(client: TestClient, call) -> None:
    call.emit("call_started", patient="Ana")
    body = client.get(f"/calls/{call.id}/trace").json()

    assert body["patient"] == "Ana"
    assert [e["type"] for e in body["trace"]] == ["call_started"]


def test_calls_rejects_a_patient_id_that_is_not_a_uuid(client: TestClient) -> None:
    assert client.post("/calls", json={"patient_id": "does-not-exist"}).status_code == 422


def test_calls_needs_a_name_and_a_phone_when_the_patient_is_unknown(client: TestClient) -> None:
    body = {"patient_id": "00000000-0000-4000-8000-000000000000"}
    assert client.post("/calls", json=body).status_code == 400


def test_without_a_database_the_store_is_the_seed(client: TestClient) -> None:
    health = client.get("/health").json()
    assert health["store"] == "seed"

    unknown = client.get("/patients/00000000-0000-4000-8000-000000000000/facts")
    assert unknown.status_code == 200
    assert unknown.json()["facts"] == []

    assert [p["name"] for p in client.get("/patients").json()] == ["Ana"]
