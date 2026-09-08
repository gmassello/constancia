import importlib

import pytest
from pydantic import ValidationError

REQUIRED = [
    "GEMINI_API_KEY",
    "ASSEMBLYAI_API_KEY",
    "ELEVENLABS_API_KEY",
    "ELEVENLABS_VOICE_ID",
    "TWILIO_ACCOUNT_SID",
    "TWILIO_AUTH_TOKEN",
    "TWILIO_NUMBER",
    "PUBLIC_BASE_URL",
]


def test_importing_the_app_without_env_does_not_raise() -> None:
    for module in ("app.main", "app.orchestrator", "app.channel", "app.llm", "app.telephony"):
        assert importlib.import_module(module)


def test_the_app_starts_and_serves_the_seed_with_no_env(monkeypatch: pytest.MonkeyPatch) -> None:
    from fastapi.testclient import TestClient

    from app.config import get_settings
    from app.main import app

    for key in [*REQUIRED, "DATABASE_URL"]:
        monkeypatch.delenv(key, raising=False)
    monkeypatch.chdir("/")
    get_settings.cache_clear()
    try:
        with TestClient(app) as client:
            health = client.get("/health").json()
            assert health["status"] == "ok"
            assert health["store"] == "seed"
            assert health["live"] is False
    finally:
        get_settings.cache_clear()


def test_settings_without_secrets_refuses_to_build(monkeypatch: pytest.MonkeyPatch) -> None:
    from app.config import Settings

    for key in REQUIRED:
        monkeypatch.delenv(key, raising=False)
    with pytest.raises(ValidationError):
        Settings(_env_file=None)


def test_e164_is_validated(monkeypatch: pytest.MonkeyPatch) -> None:
    from app.config import Settings

    for key in REQUIRED:
        monkeypatch.setenv(key, "x")
    monkeypatch.setenv("TWILIO_NUMBER", "541199999999")
    with pytest.raises(ValidationError):
        Settings(_env_file=None)

    monkeypatch.setenv("TWILIO_NUMBER", "+541199999999")
    assert Settings(_env_file=None).twilio_number == "+541199999999"
