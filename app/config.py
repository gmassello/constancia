from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

E164 = r"^\+[1-9]\d{7,14}$"
TWILIO_API_BASE = "https://api.twilio.com/"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    gemini_api_key: str
    gemini_model: str = "gemini-3.8-flash"
    gemini_embedding_model: str = "gemini-embedding-001"
    embedding_dims: int = 1536

    assemblyai_api_key: str
    assemblyai_speech_model: str = "universal-streaming-multilingual"

    elevenlabs_api_key: str
    elevenlabs_voice_id: str
    elevenlabs_model: str = "eleven_flash_v2_5"

    twilio_account_sid: str
    twilio_auth_token: str
    twilio_number: str = Field(pattern=E164)

    public_base_url: str
    validate_twilio_signature: bool = True

    database_url: str = ""

    language: str = "es"
    silence_s: float = 8.0
    barge_min_words: int = 2


@lru_cache
def get_settings() -> Settings:
    return Settings()


def is_twilio_recording(url: str) -> bool:
    return url.startswith(TWILIO_API_BASE)
