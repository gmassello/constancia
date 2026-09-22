import asyncio
from collections import Counter

import httpx

from app.config import get_settings, is_twilio_recording

API = "https://api.assemblyai.com/v2/transcript"
UPLOAD = "https://api.assemblyai.com/v2/upload"
POLL_S = 3.0
TIMEOUT_S = 180.0
# ponytail: a Twilio recording is behind Basic auth, so AssemblyAI cannot fetch it and answers 401.
# The mp3 is about a quarter of the wav, small enough to relay through one request each way.
UPLOAD_TIMEOUT_S = 120.0
MAX_NEGATIVE = 5


def request_body(url: str, language: str) -> dict:
    return {
        "audio_url": url,
        "language_code": language,
        "punctuate": True,
        "entity_detection": True,
        "sentiment_analysis": True,
    }


def summarize(payload: dict) -> dict:
    sentiments = payload.get("sentiment_analysis_results") or []
    return {
        "transcript_id": payload.get("id"),
        "entities": [
            {"text": entity["text"], "type": entity["entity_type"]}
            for entity in payload.get("entities") or []
        ],
        "sentiment": dict(Counter(item["sentiment"] for item in sentiments)),
        "negative": [
            {"text": item["text"], "confidence": item["confidence"]}
            for item in sentiments
            if item["sentiment"] == "NEGATIVE"
        ][:MAX_NEGATIVE],
    }


async def hosted(client: httpx.AsyncClient, url: str, headers: dict) -> str:
    if not is_twilio_recording(url):
        return url
    settings = get_settings()
    media = await client.get(
        f"{url}.mp3",
        auth=(settings.twilio_account_sid, settings.twilio_auth_token),
        follow_redirects=True,
    )
    media.raise_for_status()
    uploaded = await client.post(UPLOAD, headers=headers, content=media.content)
    uploaded.raise_for_status()
    return uploaded.json()["upload_url"]


async def transcribe(url: str) -> dict:
    settings = get_settings()
    headers = {"authorization": settings.assemblyai_api_key}
    async with httpx.AsyncClient(timeout=UPLOAD_TIMEOUT_S) as client:
        audio_url = await hosted(client, url, headers)
        started = await client.post(
            API, headers=headers, json=request_body(audio_url, settings.language)
        )
        started.raise_for_status()
        transcript_id = started.json()["id"]

        deadline = asyncio.get_running_loop().time() + TIMEOUT_S
        while asyncio.get_running_loop().time() < deadline:
            polled = await client.get(f"{API}/{transcript_id}", headers=headers)
            polled.raise_for_status()
            payload = polled.json()
            if payload["status"] == "completed":
                return payload
            if payload["status"] == "error":
                raise RuntimeError(payload.get("error", "assemblyai returned an error"))
            await asyncio.sleep(POLL_S)
    raise TimeoutError(f"assemblyai did not finish within {TIMEOUT_S:.0f}s")


async def run(call, store, fetch=transcribe) -> None:
    try:
        analysis = summarize(await fetch(call.recording_url))
        call.emit(
            "analysis_ready",
            entities=len(analysis["entities"]),
            sentiment=analysis["sentiment"],
        )
        if store is not None and hasattr(store, "save_analysis"):
            # ponytail: an UPDATE that matches no row does not raise, so without the count this
            # lands in the void and the only trace is the absence of one. The row is missing
            # whenever the recording webhook beats the `store` phase.
            if not await store.save_analysis(call.id, analysis):
                call.emit("warning", phase="analysis", error="no call row to attach it to")
    except Exception as exc:
        call.emit("analysis_failed", error=repr(exc))
