import pytest


@pytest.fixture(autouse=True)
def offline(monkeypatch: pytest.MonkeyPatch):
    from app.config import get_settings

    monkeypatch.setenv("GEMINI_API_KEY", "")
    monkeypatch.setenv("DATABASE_URL", "")
    monkeypatch.setenv("BARGE_MIN_WORDS", "2")
    monkeypatch.setenv("SILENCE_S", "8.0")
    monkeypatch.setenv("LANGUAGE", "en")
    monkeypatch.setenv("EMBEDDING_DIMS", "1536")
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()
