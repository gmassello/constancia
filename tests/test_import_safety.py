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
