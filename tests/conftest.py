import pytest


@pytest.fixture(autouse=True)
def offline(request: pytest.FixtureRequest, monkeypatch: pytest.MonkeyPatch):
    from app.config import get_settings

    monkeypatch.setenv("GEMINI_API_KEY", "")
    # ponytail: the integration tests are the one place a real DATABASE_URL is the point, and
    # blanking it here sent psycopg to the local socket instead of skipping — three tests that
    # could only fail, and only once somebody had docker running to notice.
    if "integration" not in request.keywords:
        monkeypatch.setenv("DATABASE_URL", "")
    monkeypatch.setenv("BARGE_MIN_WORDS", "2")
    monkeypatch.setenv("STT_CONFIDENCE_FLOOR", "0.6")
    monkeypatch.setenv("SILENCE_S", "8.0")
    monkeypatch.setenv("LANGUAGE", "en")
    monkeypatch.setenv("EMBEDDING_DIMS", "1536")
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()
