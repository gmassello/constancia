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
    missing_sid = {"RecordingUrl": url}
    response = client.post(
        "/voice/recording", data=missing_sid, headers=signed("/voice/recording", missing_sid)
    )

    assert response.status_code == 204
    assert call.recording_url is None

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


def test_scripted_rejects_a_script_that_does_not_exist(client: TestClient) -> None:
    body = {"patient_id": "8c9d0e1f-2a3b-4c5d-6e7f-8091a2b3c4d5", "script": "does-not-exist"}

    scripted = client.post("/calls", json={**body, "mode": "scripted"})
    replayed = client.post("/calls", json={**body, "mode": "replay"})

    assert scripted.status_code == 404
    assert replayed.status_code == 404
    assert client.get("/health").json()["calls"] == 0


def test_without_a_database_the_store_is_the_seed(client: TestClient) -> None:
    health = client.get("/health").json()
    assert health["store"] == "seed"

    unknown = client.get("/patients/00000000-0000-4000-8000-000000000000/facts")
    assert unknown.status_code == 200
    assert unknown.json()["facts"] == []

    assert [p["name"] for p in client.get("/patients").json()] == ["Ana"]


def test_live_dials_the_demo_phone_when_the_patient_row_has_none(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    from app.config import get_settings

    dialled: list[str] = []
    monkeypatch.setattr("app.main.place_call", lambda call_id, to: dialled.append(to) or "CA1")
    body = {"patient_id": "8c9d0e1f-2a3b-4c5d-6e7f-8091a2b3c4d5", "mode": "live"}

    monkeypatch.setenv("DEMO_PHONE", "")
    get_settings.cache_clear()
    assert client.post("/calls", json=body).status_code == 400

    monkeypatch.setenv("DEMO_PHONE", "+541199999999")
    get_settings.cache_clear()
    assert client.post("/calls", json=body).status_code == 200
    assert dialled == ["+541199999999"]


def test_status_callback_ends_a_call_nobody_answered(
    client: TestClient, call, monkeypatch: pytest.MonkeyPatch
) -> None:
    call.twilio_sid = "CA123"
    missing_sid = {"CallStatus": "failed"}
    response = client.post(
        "/voice/status", data=missing_sid, headers=signed("/voice/status", missing_sid)
    )

    assert response.status_code == 204
    assert not call.trace

    class BrokenStore:
        async def save_call(self, call) -> None:
            raise RuntimeError("store unavailable")

    monkeypatch.setattr("app.main.STORE", BrokenStore())
    form = {"CallSid": "CA123", "CallStatus": "no-answer"}
    response = client.post("/voice/status", data=form, headers=signed("/voice/status", form))

    assert response.status_code == 204
    ended = [e for e in call.trace if e["type"] == "call_ended"]
    assert len(ended) == 1
    assert ended[0]["reason"] == "no-answer"
    assert ended[0]["unanswered"] is True
    assert call.ended_at
    assert call.trace[-1]["type"] == "warning"


def test_status_callback_leaves_an_answered_call_alone(client: TestClient, call) -> None:
    call.twilio_sid = "CA123"
    form = {"CallSid": "CA123", "CallStatus": "completed"}
    response = client.post("/voice/status", data=form, headers=signed("/voice/status", form))

    assert response.status_code == 204
    assert [e for e in call.trace if e["type"] == "call_ended"] == []


def test_status_callback_does_not_emit_a_second_call_ended(client: TestClient, call) -> None:
    call.twilio_sid = "CA123"
    call.emit("call_ended", escalated=False, answers={})
    form = {"CallSid": "CA123", "CallStatus": "failed"}
    client.post("/voice/status", data=form, headers=signed("/voice/status", form))

    assert len([e for e in call.trace if e["type"] == "call_ended"]) == 1


RECORDING = "https://api.twilio.com/2010-04-01/Accounts/AC/Recordings/RE1"
PATIENT = "8c9d0e1f-2a3b-4c5d-6e7f-8091a2b3c4d5"


async def stored_call(recording_url: str | None):
    from app.calls import Call
    from app.memory import load_seed
    from app.packs import get_pack

    store = load_seed()
    call = Call(patient_id="p", patient_name="Ana", pack=get_pack("rehab"))
    call.recording_url = recording_url
    await store.save_call(call)
    return store, call


def test_the_audio_of_a_call_with_no_recording_is_a_404(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    import asyncio

    store, call = asyncio.run(stored_call(None))
    monkeypatch.setattr("app.main.STORE", store)

    response = client.get(f"/calls/{call.id}/audio")

    assert response.status_code == 404


def test_the_audio_of_an_unknown_call_is_a_404(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    from app.memory import load_seed

    monkeypatch.setattr("app.main.STORE", load_seed())

    assert client.get("/calls/nope/audio").status_code == 404


def test_a_recording_url_that_is_not_twilios_is_refused(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    import asyncio

    store, call = asyncio.run(stored_call("https://evil.example.com/a.mp3"))
    monkeypatch.setattr("app.main.STORE", store)

    response = client.get(f"/calls/{call.id}/audio")

    assert response.status_code == 400


def test_the_recording_is_relayed_with_twilio_auth(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    import asyncio

    import httpx

    store, call = asyncio.run(stored_call(RECORDING))
    monkeypatch.setattr("app.main.STORE", store)
    asked = {}

    class FakeClient:
        def __init__(self, *args, **kwargs) -> None:
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, *args) -> None:
            return None

        async def get(self, url, **kwargs):
            asked["url"] = url
            asked["auth"] = kwargs.get("auth")
            return httpx.Response(200, content=b"ID3mp3bytes")

    monkeypatch.setattr("app.main.httpx.AsyncClient", FakeClient)

    response = client.get(f"/calls/{call.id}/audio")

    assert response.status_code == 200
    assert response.headers["content-type"] == "audio/mpeg"
    assert response.content == b"ID3mp3bytes"
    assert asked["url"] == f"{RECORDING}.mp3"
    assert asked["auth"] == ("x", AUTH_TOKEN)


def test_twilio_refusing_the_recording_is_a_502(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    import asyncio

    import httpx

    store, call = asyncio.run(stored_call(RECORDING))
    monkeypatch.setattr("app.main.STORE", store)

    class FakeClient:
        def __init__(self, *args, **kwargs) -> None:
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, *args) -> None:
            return None

        async def get(self, url, **kwargs):
            return httpx.Response(404)

    monkeypatch.setattr("app.main.httpx.AsyncClient", FakeClient)

    assert client.get(f"/calls/{call.id}/audio").status_code == 502


def seeded_store():
    from app.memory import load_seed

    return load_seed()


def test_the_questions_of_a_patient_come_back_newest_first(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr("app.main.STORE", seeded_store())

    rows = client.get(f"/patients/{PATIENT}/questions").json()

    assert [row["status"] for row in rows] == ["answered", "open"]


def test_answering_an_open_question_returns_its_new_status(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    store = seeded_store()
    monkeypatch.setattr("app.main.STORE", store)
    open_id = next(r["id"] for r in store.questions_rows if r["status"] == "open")

    response = client.post(f"/questions/{open_id}/answer", json={"answer": "Ice is fine."})

    assert response.status_code == 200
    assert response.json() == {"question_id": open_id, "status": "answered"}


def test_answering_a_question_twice_is_a_409(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    store = seeded_store()
    monkeypatch.setattr("app.main.STORE", store)
    open_id = next(r["id"] for r in store.questions_rows if r["status"] == "open")
    client.post(f"/questions/{open_id}/answer", json={"answer": "Ice is fine."})

    again = client.post(f"/questions/{open_id}/answer", json={"answer": "Actually no."})

    assert again.status_code == 409


def test_an_empty_answer_is_refused(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    store = seeded_store()
    monkeypatch.setattr("app.main.STORE", store)
    open_id = next(r["id"] for r in store.questions_rows if r["status"] == "open")

    assert client.post(f"/questions/{open_id}/answer", json={"answer": ""}).status_code == 422


def test_dismissing_an_open_question_works_once(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    store = seeded_store()
    monkeypatch.setattr("app.main.STORE", store)
    open_id = next(r["id"] for r in store.questions_rows if r["status"] == "open")

    assert client.post(f"/questions/{open_id}/dismiss").status_code == 200
    assert client.post(f"/questions/{open_id}/dismiss").status_code == 409
