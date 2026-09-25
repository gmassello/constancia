import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import httpx  # noqa: E402

from app import commitments, jev  # noqa: E402
from app.config import settings_or_none  # noqa: E402
from app.packs import get_pack  # noqa: E402

QUOTES = [
    ("I will do the exercises every day this week", "rehab"),
    ("I'm going to go back to physio on Monday", "rehab"),
    ("I will feed him on both sides every night", "postpartum"),
    ("I am going to check my sugar before breakfast", "chronic"),
    ("I will log my blood pressure every morning", "chronic"),
    ("I will take the pram to the corner every afternoon", "postpartum"),
    ("I will keep the compression stockings on all day", "rehab"),
    ("I will put my feet up whenever I sit down", "rehab"),
    ("I will keep the wound dry until Friday", "postpartum"),
    ("I'll be at the conference next week", "rehab"),
    ("I will watch the match on Sunday", "rehab"),
    ("I will call my brother tonight", "rehab"),
    ("I will paint the kitchen this weekend", "rehab"),
]

# The first five are scored by a vocabulary and never posted. The eight after them are what actually
# reaches Jev: four promises about the patient's own care, and four everyday plans that are not.


async def probe(client: httpx.AsyncClient, key: str, quote: str, s) -> tuple[str, float | None]:
    response = await client.post(
        jev.ENDPOINT,
        json=jev.payload(quote, s.jev_zero_retention),
        headers={"Authorization": f"Bearer {key}"},
    )
    if response.status_code != 200:
        return f"{response.status_code} {response.json().get('error', {}).get('type', '')}", None
    return "200", response.json()["answers"][jev.KEY]["probability"]


async def main() -> None:
    settings = settings_or_none()
    if not settings or not settings.ai_gateway_api_key:
        print("no AI_GATEWAY_API_KEY: the second opinion is off and the vocabulary decides alone")
        return
    print(f"model {jev.MODEL}  floor {settings.jev_floor}\n")
    print(f"{'vocab':>6}  {'prob':>5}  {'status':>16}  {'verdict':>8}  {'pack':>10}  quote")
    async with httpx.AsyncClient(timeout=10.0) as client:
        for quote, key in QUOTES:
            local = commitments.confidence(quote, get_pack(key))
            status, prob = (
                ("not asked", None)
                if local is not None
                else await probe(client, settings.ai_gateway_api_key, quote, settings)
            )
            rescued = prob is not None and prob >= settings.jev_floor
            verdict = "kept" if local is not None else "rescued" if rescued else "dropped"
            print(
                f"{'-' if local is None else local:>6}  "
                f"{'-' if prob is None else f'{prob:.2f}':>5}  "
                f"{status:>16}  {verdict:>8}  {key:>10}  {quote}"
            )


if __name__ == "__main__":
    asyncio.run(main())
