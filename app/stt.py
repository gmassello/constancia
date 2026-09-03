import contextlib
import json
from collections.abc import AsyncIterator
from urllib.parse import urlencode

from websockets.asyncio.client import ClientConnection, connect

from app.config import get_settings

STREAMING_URL = "wss://streaming.assemblyai.com/v3/ws"
MAX_KEYTERMS = 100


def stream_url(keyterms: list[str] | None = None) -> str:
    settings = get_settings()
    params = {
        "sample_rate": 8000,
        "encoding": "pcm_mulaw",
        "speech_model": settings.assemblyai_speech_model,
        "language_codes": json.dumps([settings.language]),
        "format_turns": "true",
    }
    if keyterms:
        params["keyterms_prompt"] = json.dumps(keyterms[:MAX_KEYTERMS])
    return f"{STREAMING_URL}?{urlencode(params)}"


class StreamingSTT:
    def __init__(self, keyterms: list[str] | None = None) -> None:
        self.keyterms = keyterms or []
        self.ws: ClientConnection | None = None

    async def connect(self) -> None:
        self.ws = await connect(
            stream_url(self.keyterms),
            additional_headers={"Authorization": get_settings().assemblyai_api_key},
            max_size=None,
        )

    async def feed(self, audio: bytes) -> None:
        if self.ws:
            await self.ws.send(audio)

    async def update_keyterms(self, terms: list[str]) -> None:
        self.keyterms = terms
        if self.ws:
            await self.ws.send(
                json.dumps({"type": "UpdateConfiguration", "keyterms_prompt": terms[:MAX_KEYTERMS]})
            )

    async def messages(self) -> AsyncIterator[dict]:
        if not self.ws:
            return
        async for raw in self.ws:
            if isinstance(raw, bytes):
                continue
            yield json.loads(raw)

    async def terminate(self) -> None:
        if not self.ws:
            return
        with contextlib.suppress(Exception):
            await self.ws.send(json.dumps({"type": "Terminate"}))
        await self.ws.close()
        self.ws = None
