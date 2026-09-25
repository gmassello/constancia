import asyncio
import hashlib
import json
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import httpx  # noqa: E402

from app import commitments, jev  # noqa: E402
from app.config import settings_or_none  # noqa: E402
from app.packs import get_pack  # noqa: E402

PROMISE = True
EVERYDAY = False

QUOTES = [
    ("I will do the exercises every day this week", "rehab", PROMISE),
    ("I'm going to go back to physio on Monday", "rehab", PROMISE),
    ("I will feed him on both sides every night", "postpartum", PROMISE),
    ("I am going to check my sugar before breakfast", "chronic", PROMISE),
    ("I will log my blood pressure every morning", "chronic", PROMISE),
    ("I will take the pram to the corner every afternoon", "postpartum", PROMISE),
    ("I will keep the compression stockings on all day", "rehab", PROMISE),
    ("I will put my feet up whenever I sit down", "rehab", PROMISE),
    ("I will keep the wound dry until Friday", "postpartum", PROMISE),
    ("I'll be at the conference next week", "rehab", EVERYDAY),
    ("I will watch the match on Sunday", "rehab", EVERYDAY),
    ("I will call my brother tonight", "rehab", EVERYDAY),
    ("I will paint the kitchen this weekend", "rehab", EVERYDAY),
]

RECORD = Path(__file__).resolve().parent / "jev-measured.json"


def wording() -> str:
    text = json.dumps([jev.INSTRUCTIONS, jev.CRITERIA], sort_keys=True)
    return hashlib.sha256(text.encode()).hexdigest()[:12]


async def probe(client: httpx.AsyncClient, key: str, quote: str, s) -> tuple[str, float | None]:
    response = await client.post(
        jev.ENDPOINT,
        json=jev.payload(quote, s.jev_zero_retention),
        headers={"Authorization": f"Bearer {key}"},
    )
    if response.status_code != 200:
        return f"{response.status_code} {response.json().get('error', {}).get('type', '')}", None
    return "200", response.json()["answers"][jev.KEY]["probability"]


def summarise(rows: list[dict], floor: float) -> dict:
    asked = [r for r in rows if r["prob"] is not None]
    promises = [r for r in asked if r["expected"]]
    rescued = [r for r in asked if r["verdict"] == "rescued"]
    found = [r for r in promises if r["verdict"] == "rescued"]
    missed = [r["quote"] for r in promises if r["verdict"] != "rescued"]
    wrong = [r["quote"] for r in rescued if not r["expected"]]
    everyday = [r["prob"] for r in asked if not r["expected"]]
    # ponytail: the margin is written the way the floor was chosen — how far the floor sits above
    # the best-scoring everyday plan. It is the number that says whether 0.8 is defensible, and it
    # is meaningless on a run where nothing was asked, which is why it is None there.
    return {
        "asked": len(asked),
        "recall": round(len(found) / len(promises), 2) if promises else None,
        "precision": round(len(found) / len(rescued), 2) if rescued else None,
        "margin": round(floor - max(everyday), 2) if everyday else None,
        "worst_promise": min((r["prob"] for r in promises), default=None),
        "best_everyday": max(everyday, default=None),
        "missed": missed,
        "wrong": wrong,
        "vocabulary_kept": sum(1 for r in rows if r["vocab"] is not None),
        "vocabulary_wrong": [
            r["quote"] for r in rows if r["vocab"] is not None and not r["expected"]
        ],
    }


async def main() -> None:
    settings = settings_or_none()
    if not settings or not settings.ai_gateway_api_key:
        print("no AI_GATEWAY_API_KEY: the second opinion is off and the vocabulary decides alone")
        return
    floor = settings.jev_floor
    print(f"model {jev.MODEL}  floor {floor}  wording {wording()}\n")
    header = f"{'want':>8}  {'vocab':>6}  {'prob':>5}  {'status':>16}  {'verdict':>8}"
    print(f"{header}  {'pack':>10}  quote")
    rows: list[dict] = []
    async with httpx.AsyncClient(timeout=10.0) as client:
        for quote, key, expected in QUOTES:
            local = commitments.confidence(quote, get_pack(key))
            status, prob = (
                ("not asked", None)
                if local is not None
                else await probe(client, settings.ai_gateway_api_key, quote, settings)
            )
            rescued = prob is not None and prob >= floor
            verdict = "kept" if local is not None else "rescued" if rescued else "dropped"
            rows.append(
                {
                    "quote": quote,
                    "pack": key,
                    "expected": expected,
                    "vocab": local,
                    "prob": prob,
                    "status": status,
                    "verdict": verdict,
                }
            )
            print(
                f"{'promise' if expected else 'everyday':>8}  "
                f"{'-' if local is None else local:>6}  "
                f"{'-' if prob is None else f'{prob:.2f}':>5}  "
                f"{status:>16}  {verdict:>8}  {key:>10}  {quote}"
            )

    found = summarise(rows, floor)
    print(f"\n{found['asked']} asked, {found['vocabulary_kept']} taken by the vocabulary")
    print(f"recall {found['recall']}  precision {found['precision']}  margin {found['margin']}")
    if found["worst_promise"] is not None:
        print(f"worst promise {found['worst_promise']}  best everyday {found['best_everyday']}")
    for quote in found["missed"]:
        print(f"  missed    {quote}")
    for quote in found["wrong"]:
        print(f"  false     {quote}")
    for quote in found["vocabulary_wrong"]:
        print(f"  vocab hit {quote}")

    RECORD.write_text(
        json.dumps(
            {
                "measured": date.today().isoformat(),
                "model": jev.MODEL,
                "floor": floor,
                "wording": wording(),
                "summary": found,
                "rows": rows,
            },
            indent=2,
        )
        + "\n"
    )
    print(f"\nwritten to scripts/{RECORD.name}")


if __name__ == "__main__":
    asyncio.run(main())
