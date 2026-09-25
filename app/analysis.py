import asyncio
import re
from collections import Counter

import httpx

from app.config import get_settings, is_twilio_recording
from app.guard import normalize

API = "https://api.assemblyai.com/v2/transcript"
UPLOAD = "https://api.assemblyai.com/v2/upload"
POLL_S = 3.0
TIMEOUT_S = 180.0
# ponytail: a Twilio recording is behind Basic auth, so AssemblyAI cannot fetch it and answers 401.
# The mp3 is about a quarter of the wav, small enough to relay through one request each way.
UPLOAD_TIMEOUT_S = 120.0
MAX_NEGATIVE = 5
MAX_PHRASES = 10
MATCH_FLOOR = 0.7
WORD = re.compile(r"[a-z0-9']+")


def request_body(url: str, language: str) -> dict:
    return {
        "audio_url": url,
        "language_code": language,
        "punctuate": True,
        "entity_detection": True,
        "sentiment_analysis": True,
        "auto_highlights": True,
    }


def phrases(payload: dict) -> list[dict]:
    # ponytail: the results arrive in the order they were spoken, so the rank is what orders them
    # and then it is dropped — the panel shows the phrase and how often it was said, and the next
    # call takes the top of the list. Keep the rank the day something wants a floor, not a cap.
    found = (payload.get("auto_highlights_result") or {}).get("results") or []
    ranked = sorted(found, key=lambda item: item.get("rank") or 0.0, reverse=True)
    return [{"text": item["text"], "count": item["count"]} for item in ranked[:MAX_PHRASES]]


def summarize(payload: dict) -> dict:
    sentiments = payload.get("sentiment_analysis_results") or []
    return {
        "transcript_id": payload.get("id"),
        "entities": [
            {"text": entity["text"], "type": entity["entity_type"]}
            for entity in payload.get("entities") or []
        ],
        "sentiment": dict(Counter(item["sentiment"] for item in sentiments)),
        "phrases": phrases(payload),
        "negative": [
            {"text": item["text"], "confidence": item["confidence"]}
            for item in sentiments
            if item["sentiment"] == "NEGATIVE"
        ][:MAX_NEGATIVE],
    }


def _tokens(text: str) -> list[str]:
    return WORD.findall(normalize(text))


def locate(quote: str, words: list[dict]) -> tuple[int, int] | None:
    # ponytail: a straight sliding window, because a quote is under a dozen tokens and a call under
    # a thousand. It compares tokens for equality, so a word the streaming pass and the recorded
    # pass spell differently costs one hit rather than the whole match. Anything smarter than this
    # needs an edit distance, and nothing here is long enough to pay for one.
    needle = _tokens(quote)
    hay = [_tokens(word.get("text", "")) for word in words]
    hay = ["".join(parts) for parts in hay]
    if not needle or len(hay) < len(needle):
        return None
    best, at = 0.0, -1
    for start in range(len(hay) - len(needle) + 1):
        window = hay[start : start + len(needle)]
        score = sum(1 for a, b in zip(needle, window, strict=True) if a == b) / len(needle)
        if score > best:
            best, at = score, start
    if at < 0 or best < MATCH_FLOOR:
        return None
    first, last = words[at], words[at + len(needle) - 1]
    return int(first["start"]), int(last["end"])


async def anchor(call, store, words: list[dict]) -> int:
    if not words or store is None or not hasattr(store, "set_fact_span"):
        return 0
    rows = [r for r in await store.chain(call.patient_id) if str(r["call_id"]) == str(call.id)]
    anchored = 0
    for row in rows:
        span = locate(str(row["quote"]), words)
        if span is None:
            continue
        await store.set_fact_span(str(row["id"]), *span)
        anchored += 1
    return anchored


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


async def transcribe(url: str, extra: dict | None = None) -> dict:
    settings = get_settings()
    headers = {"authorization": settings.assemblyai_api_key}
    async with httpx.AsyncClient(timeout=UPLOAD_TIMEOUT_S) as client:
        audio_url = await hosted(client, url, headers)
        started = await client.post(
            API, headers=headers, json=request_body(audio_url, settings.language) | (extra or {})
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
        payload = await fetch(call.recording_url)
        analysis = summarize(payload)
        call.emit(
            "analysis_ready",
            entities=len(analysis["entities"]),
            sentiment=analysis["sentiment"],
        )
        # ponytail: the word timings are used and thrown away rather than stored on the call row.
        # Every fact that aligns keeps its own span, which is all the panel reads; keeping the
        # whole list would put a thousand objects in `calls.analysis` for one play button.
        anchored = await anchor(call, store, payload.get("words") or [])
        if anchored:
            call.emit("quotes_anchored", facts=anchored)
        if store is not None and hasattr(store, "save_analysis"):
            # ponytail: an UPDATE that matches no row does not raise, so without the count this
            # lands in the void and the only trace is the absence of one. The row is missing
            # whenever the recording webhook beats the `store` phase.
            if not await store.save_analysis(call.id, analysis):
                call.emit("warning", phase="analysis", error="no call row to attach it to")
    except Exception as exc:
        call.emit("analysis_failed", error=repr(exc))
