import pytest


@pytest.fixture(autouse=True)
def offline(monkeypatch: pytest.MonkeyPatch):
    from app.config import get_settings

    monkeypatch.setenv("GEMINI_API_KEY", "")
    monkeypatch.setenv("DATABASE_URL", "")
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()
