from collections.abc import AsyncIterator

import httpx

from app.config import get_settings

BASE_URL = "https://api.elevenlabs.io/v1/text-to-speech"
TIMEOUT_S = 30.0
MP3_MAGIC = (b"ID3", b"\xff\xfb", b"\xff\xf3")


async def stream(text: str) -> AsyncIterator[bytes]:
    settings = get_settings()
    url = f"{BASE_URL}/{settings.elevenlabs_voice_id}/stream"
    payload = {"text": text, "model_id": settings.elevenlabs_model}
    headers = {"xi-api-key": settings.elevenlabs_api_key}
    params = {"output_format": "ulaw_8000"}

    async with httpx.AsyncClient(timeout=TIMEOUT_S) as client:
        async with client.stream(
            "POST", url, json=payload, headers=headers, params=params
        ) as response:
            response.raise_for_status()
            async for chunk in response.aiter_bytes():
                if chunk:
                    yield chunk


def looks_like_mp3(chunk: bytes) -> bool:
    return chunk.startswith(MP3_MAGIC)
