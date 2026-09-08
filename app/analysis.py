import asyncio
from collections import Counter

import httpx

from app.config import get_settings

API = "https://api.assemblyai.com/v2/transcript"
POLL_S = 3.0
TIMEOUT_S = 180.0
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


async def transcribe(url: str) -> dict:
    settings = get_settings()
    headers = {"authorization": settings.assemblyai_api_key}
    async with httpx.AsyncClient(timeout=30.0) as client:
        started = await client.post(
            API, headers=headers, json=request_body(url, settings.language)
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
            await store.save_analysis(call.id, analysis)
    except Exception as exc:
        call.emit("analysis_failed", error=repr(exc))
